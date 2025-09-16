import logging
import statistics
import math
import json

from enum import IntEnum
from typing import Dict, Optional, Sequence, Any
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from protocol_adapter.lem_report.const import AutoCheckAction, AutoCheckResult
from protocol_adapter.lem_report.models import ReportTask, ReportTaskSpec, ReportType
from protocol_adapter.lem_report.models_payload import AutoCheckData, NoiseDetail, VibrationDetail
from protocol_adapter.lem_report.service import ReportService
from protocol_adapter.protobuf_wrapper import monitor_pb2
from protocol_adapter.utils.misc import MiscUtils

_logger = logging.getLogger(__name__)


# 注意上报任务的 uniformID 使用 atype << 8 + sensor_id 来合并去重
class SensorID(IntEnum):
    Undefined = 0
    MotorLift = 1
    MotorRotate = 2
    MotorLeft = 3
    MotorRight = 4
    Motorfront = 5
    Noise_1 = 6
    Vibration_1 = 7
    LoadUnit_1 = 8
    SvcUp = 11
    SvcDown = 12


class AlertType(IntEnum):
    Undefined = 0
    OffsetLarge = 1  # 偏载过远
    OverloadWeight = 2  # 重量超载
    MotorCurrent = 3  # 电机电流过大
    MotorTemprature = 4  # 电机温度过高
    Vibration = 5  # 震动过大
    Noise = 6  # 噪音过大
    SN_Invalid = 11  # 上视货码异常
    DmcodeInvalid = 12  # 下视地码异常


class AlertLevel(IntEnum):
    NORMAL = 0
    WARNING = 1
    CRITICAL = 2


@dataclass
class SensorAlert:
    sensor_id: SensorID
    level: AlertLevel
    atype: AlertType
    value: Any = None
    message: str = ''
    timestamp_us: int = 0

    @property
    def uniform_id(self) -> int:
        return self.atype << 8 + self.sensor_id


MAX_QUEUE_SAMPLES_PER_SENSOR_FOR_CHECK = 2000

THRESHOLDS = {
    SensorID.Vibration_1: {  # 震动加速度, g
        'warning': 5.0,
        'critical': 10.0,
    },
    SensorID.Noise_1: {  # 噪音分贝: db
        'warning': 65.0,
        'critical': 75.0,
    },
    SensorID.LoadUnit_1: {  # 重量 kg, 偏移 m
        'weight_warning': 400.0,
        'weight_critical': 450.0,
        'offset_warning': 0.3,
        'offset_critical': 0.5,
        'offset_weight_threshold': 5,  # 需要考虑偏载的最小重量
    },
    SensorID.MotorLift: {  # 电流 A, 温度 ℃
        'current_warning': 15.0,
        'current_critical': 20.0,
        'temperature_warning': 80.0,
        'temperature_critical': 100.0,
    },
    SensorID.MotorRotate: {
        'current_warning': 15.0,
        'current_critical': 20.0,
        'temperature_warning': 80.0,
        'temperature_critical': 100.0,
    },
    SensorID.MotorLeft: {
        'current_warning': 15.0,
        'current_critical': 20.0,
        'temperature_warning': 80.0,
        'temperature_critical': 100.0,
    },
    SensorID.MotorRight: {
        'current_warning': 15.0,
        'current_critical': 20.0,
        'temperature_warning': 80.0,
        'temperature_critical': 100.0,
    },
}

SENSOR_ID_TO_SAMPLES_FIELD = {
    SensorID.Vibration_1: 'vibration_1',
    SensorID.Noise_1: 'noise_1',
    SensorID.LoadUnit_1: 'loadunit_1',
    SensorID.MotorLift: 'motor_lift',
    SensorID.MotorRotate: 'motor_rotate',
    SensorID.MotorLeft: 'motor_left',
    SensorID.MotorRight: 'motor_right',
}


@dataclass
class SamplesDeque:
    vibration_1 = deque(maxlen=MAX_QUEUE_SAMPLES_PER_SENSOR_FOR_CHECK)
    noise_1 = deque(maxlen=MAX_QUEUE_SAMPLES_PER_SENSOR_FOR_CHECK)
    loadunit_1 = deque(maxlen=MAX_QUEUE_SAMPLES_PER_SENSOR_FOR_CHECK)
    motor_lift = deque(maxlen=MAX_QUEUE_SAMPLES_PER_SENSOR_FOR_CHECK)
    motor_rotate = deque(maxlen=MAX_QUEUE_SAMPLES_PER_SENSOR_FOR_CHECK)
    motor_left = deque(maxlen=MAX_QUEUE_SAMPLES_PER_SENSOR_FOR_CHECK)
    motor_right = deque(maxlen=MAX_QUEUE_SAMPLES_PER_SENSOR_FOR_CHECK)


class SensorSampleUtils:
    @classmethod
    def get_freq_by_ts(cls, queue: Sequence) -> float:
        """获取采样频率"""
        if len(queue) > 1:
            dt = (queue[-1].timestamp_us - queue[0].timestamp_us) / (len(queue) - 1)
            return 1e6 / dt if dt > 0 else 0
        return 0

    @classmethod
    def get_sample_overview(cls, sensor_id: SensorID, samples: Sequence, avg_time: float = 0.5):
        # 滑动平均: 取 avg_time 时间的采样平均，默认 0.5s
        freq = cls.get_freq_by_ts(samples)
        avg_size = max(math.ceil(freq * avg_time), 1)
        avg_deque = deque(maxlen=avg_size)

        # 打印调试信息
        # head_tail = f'\n{samples[0]}..\n{samples[-1]}' if len(samples) else ''
        # _logger.debug(f'#{sensor_id.name}: size={len(samples)} freq={freq:.2f}{head_tail}')

        return freq, avg_deque

    @classmethod
    def get_average_noise(cls, queue: Sequence[monitor_pb2.NoiseSensor]) -> monitor_pb2.NoiseSensor:
        return monitor_pb2.NoiseSensor(
            timestamp_us=max(s.timestamp_us for s in queue),
            noise_db=statistics.mean(s.noise_db for s in queue),
        )

    @classmethod
    def get_average_loadunit(
        cls, queue: Sequence[monitor_pb2.LoadUnitSensor]
    ) -> monitor_pb2.LoadUnitSensor:
        return monitor_pb2.LoadUnitSensor(
            timestamp_us=max(s.timestamp_us for s in queue),
            weight_kg=statistics.mean(s.weight_kg for s in queue),
            offset_m=statistics.mean(s.offset_m for s in queue),
            angle_rad=statistics.mean(s.angle_rad for s in queue),
        )

    @classmethod
    def get_average_vibration(
        cls, queue: Sequence[monitor_pb2.VibrationSensor]
    ) -> monitor_pb2.VibrationSensor:
        return monitor_pb2.VibrationSensor(
            timestamp_us=max(s.timestamp_us for s in queue),
            x_ac_g=statistics.mean(s.x_ac_g for s in queue),
            y_ac_g=statistics.mean(s.y_ac_g for s in queue),
            z_ac_g=statistics.mean(s.z_ac_g for s in queue),
        )

    @classmethod
    def get_average_motor(cls, queue: Sequence[monitor_pb2.MotorSensor]) -> monitor_pb2.MotorSensor:
        return monitor_pb2.MotorSensor(
            timestamp_us=max(s.timestamp_us for s in queue),
            speed_rpm=statistics.mean(s.speed_rpm for s in queue),
            # 计算平均时，电流有正负，计算绝对大小的平均
            current_A=statistics.mean(abs(s.current_A) for s in queue),
            voltage_V=statistics.mean(s.voltage_V for s in queue),
            temperature_C=statistics.mean(s.temperature_C for s in queue),
        )


class SensorProcessorChecker(ABC, SensorSampleUtils):
    @abstractmethod
    def queue_alert(self, alert: SensorAlert):
        pass

    def check_noise(self, sensor_id: SensorID, samples: Sequence[monitor_pb2.NoiseSensor]):
        _, avg_deque = self.get_sample_overview(sensor_id, samples)

        for sample in samples:
            avg_deque.append(sample)
            avg = self.get_average_noise(avg_deque)

            if avg.noise_db >= THRESHOLDS[sensor_id]['critical']:
                self.queue_alert(
                    alert=SensorAlert(
                        sensor_id=sensor_id,
                        level=AlertLevel.CRITICAL,
                        atype=AlertType.Noise,
                        value=avg,
                        message=(f'#{sensor_id} 噪音超限: {avg.noise_db:.2f}db'),
                        timestamp_us=avg.timestamp_us,
                    )
                )
            elif avg.noise_db >= THRESHOLDS[sensor_id]['warning']:
                self.queue_alert(
                    alert=SensorAlert(
                        sensor_id=sensor_id,
                        level=AlertLevel.WARNING,
                        atype=AlertType.Noise,
                        value=avg,
                        message=(f'#{sensor_id} 噪音告警: {avg.noise_db:.2f}db'),
                        timestamp_us=avg.timestamp_us,
                    )
                )

    def check_loadunit(self, sensor_id: SensorID, samples: Sequence[monitor_pb2.LoadUnitSensor]):
        _, avg_deque = self.get_sample_overview(sensor_id, samples)

        for sample in samples:
            avg_deque.append(sample)
            avg = self.get_average_loadunit(avg_deque)

            # 重量超过阀值时，才考虑偏载距离
            if avg.weight_kg > THRESHOLDS[sensor_id]['offset_weight_threshold']:
                if avg.offset_m >= THRESHOLDS[sensor_id]['offset_critical']:
                    self.queue_alert(
                        alert=SensorAlert(
                            sensor_id=sensor_id,
                            level=AlertLevel.CRITICAL,
                            atype=AlertType.OffsetLarge,
                            value=avg,
                            message=(
                                f'#{sensor_id} 偏载距离超限: {avg.offset_m:.2f}m '
                                f'({avg.weight_kg:.2f}kg, {avg.angle_rad:.2f}rad)'
                            ),
                            timestamp_us=avg.timestamp_us,
                        )
                    )
                elif avg.offset_m >= THRESHOLDS[sensor_id]['offset_warning']:
                    self.queue_alert(
                        alert=SensorAlert(
                            sensor_id=sensor_id,
                            level=AlertLevel.WARNING,
                            atype=AlertType.OffsetLarge,
                            value=avg,
                            message=(
                                f'#{sensor_id} 偏载距离告警: {avg.offset_m:.2f}m '
                                f'({avg.weight_kg:.2f}kg, {avg.angle_rad:.2f}rad)'
                            ),
                            timestamp_us=avg.timestamp_us,
                        )
                    )

            if avg.weight_kg >= THRESHOLDS[sensor_id]['weight_critical']:
                self.queue_alert(
                    alert=SensorAlert(
                        sensor_id=sensor_id,
                        level=AlertLevel.CRITICAL,
                        atype=AlertType.OverloadWeight,
                        value=avg,
                        message=(
                            f'#{sensor_id} 载荷重量超限: {avg.weight_kg:.2f}kg '
                            f'({avg.offset_m:.2f}m, {avg.angle_rad:.2f}rad)'
                        ),
                        timestamp_us=avg.timestamp_us,
                    )
                )
            elif avg.weight_kg >= THRESHOLDS[sensor_id]['weight_warning']:
                self.queue_alert(
                    alert=SensorAlert(
                        sensor_id=sensor_id,
                        level=AlertLevel.WARNING,
                        atype=AlertType.OverloadWeight,
                        value=avg,
                        message=(
                            f'#{sensor_id} 载荷重量告警: {avg.weight_kg:.2f}kg '
                            f'({avg.offset_m:.2f}m, {avg.angle_rad:.2f}rad)'
                        ),
                        timestamp_us=avg.timestamp_us,
                    )
                )

    def check_vibration(self, sensor_id: SensorID, samples: Sequence[monitor_pb2.VibrationSensor]):
        """检查振动数据是否超过阈值"""
        _, avg_deque = self.get_sample_overview(sensor_id, samples)

        for sample in samples:
            # z 轴减去固定的地球引力加速度
            sample.z_ac_g -= 1

            avg_deque.append(sample)
            avg = self.get_average_vibration(avg_deque)

            max_ac = max(abs(avg.x_ac_g), abs(avg.y_ac_g), abs(avg.z_ac_g))

            if max_ac >= THRESHOLDS[sensor_id]['critical']:
                self.queue_alert(
                    alert=SensorAlert(
                        sensor_id=sensor_id,
                        level=AlertLevel.CRITICAL,
                        atype=AlertType.Vibration,
                        value=avg,
                        message=(
                            f'#{sensor_id} 振动超限: {max_ac:.2f}g '
                            f'({avg.x_ac_g:.2f}, {avg.y_ac_g:.2f}, {avg.z_ac_g:.2f}) g'
                        ),
                        timestamp_us=avg.timestamp_us,
                    )
                )
            elif max_ac >= THRESHOLDS[sensor_id]['warning']:
                self.queue_alert(
                    alert=SensorAlert(
                        sensor_id=sensor_id,
                        level=AlertLevel.WARNING,
                        atype=AlertType.Vibration,
                        value=avg,
                        message=(
                            f'#{sensor_id} 振动告警: {max_ac:.2f}g '
                            f'({avg.x_ac_g:.2f}, {avg.y_ac_g:.2f}, {avg.z_ac_g:.2f}) g'
                        ),
                        timestamp_us=avg.timestamp_us,
                    )
                )

    def check_motor(self, sensor_id: SensorID, samples: Sequence[monitor_pb2.MotorSensor]):
        """检查电机数据是否超过阈值"""
        _, avg_deque = self.get_sample_overview(sensor_id, samples)

        for sample in samples:
            # 取滑动平均，注意: 电流平均取的是绝对平均，样本数据有正负
            avg_deque.append(sample)
            avg = self.get_average_motor(avg_deque)

            # 检查温度
            if avg.temperature_C >= THRESHOLDS[sensor_id]['temperature_critical']:
                self.queue_alert(
                    alert=SensorAlert(
                        sensor_id=sensor_id,
                        level=AlertLevel.CRITICAL,
                        atype=AlertType.MotorTemprature,
                        value=avg,
                        message=f'#{sensor_id} 电机温度超限: {avg.temperature_C:.2f}℃',
                        timestamp_us=avg.timestamp_us,
                    )
                )
            elif avg.temperature_C >= THRESHOLDS[sensor_id]['temperature_warning']:
                self.queue_alert(
                    alert=SensorAlert(
                        sensor_id=sensor_id,
                        level=AlertLevel.WARNING,
                        atype=AlertType.MotorTemprature,
                        value=avg,
                        message=f'#{sensor_id} 电机温度告警: {avg.temperature_C:.2f}℃',
                        timestamp_us=avg.timestamp_us,
                    )
                )

            # 检查电流
            if avg.current_A >= THRESHOLDS[sensor_id]['current_critical']:
                self.queue_alert(
                    alert=SensorAlert(
                        sensor_id=sensor_id,
                        level=AlertLevel.CRITICAL,
                        atype=AlertType.MotorCurrent,
                        value=avg,
                        message=f'#{sensor_id} 电机电流超限: {avg.current_A:.2f}A',
                        timestamp_us=avg.timestamp_us,
                    )
                )
            elif avg.current_A >= THRESHOLDS[sensor_id]['current_warning']:
                self.queue_alert(
                    alert=SensorAlert(
                        sensor_id=sensor_id,
                        level=AlertLevel.WARNING,
                        atype=AlertType.MotorCurrent,
                        value=avg,
                        message=f'#{sensor_id} 电机电流告警: {avg.current_A:.2f}A',
                        timestamp_us=avg.timestamp_us,
                    )
                )


@MiscUtils.singleton()
class SensorProcessor(SensorProcessorChecker):
    def __init__(self):
        self._alerts: Dict[int, SensorAlert] = {}

        # 点检辅助记录
        self._inspection_enabled = False
        self._inspection_begin_time = None
        self._spec_for_inspection = None
        self._check_inspection_on_this_sample = False
        self._inspection_check_actions = deque()

        # 点检时缓存的采样数据
        self._queued_samples = SamplesDeque()

        # 记录最后收到的传感器采样时间
        self._last_samples_ts: Dict[SensorID, int] = {}

        # 外部调用时扔线程池
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='SensorProcessor')

    def set_inspection_state(
        self,
        *,
        enable: bool,
        spec: Optional[ReportTaskSpec] = None,
        check_actions: Sequence[AutoCheckAction] = deque(),
    ):
        if self._inspection_enabled and enable:
            _logger.warning('already enabled inspection')
            return

        _logger.info(f'set inspection enable state: {enable} ..')

        self._inspection_enabled = enable
        if enable:
            self._inspection_begin_time = datetime.now()
        elif self._inspection_begin_time:
            self._check_inspection_on_this_sample = True
            self._inspection_check_actions = check_actions
            self._spec_for_inspection = spec

    def sync_motor_sample_time(self, samples: monitor_pb2.SensorDataCollection):
        """同步电机采样数据时间"""

        # 取电机采样数据进行同步
        motor_samples = [
            getattr(samples, k) for k in samples.DESCRIPTOR.fields_by_name if k.startswith('motor_')
        ]

        # ref 参考采样序列
        ref = motor_samples[0]

        # 以 ref 为参考求采样平均周期
        if len(ref) > 1:
            d_ts = (ref[-1].timestamp_us - ref[0].timestamp_us) / (len(ref) - 1)
        else:
            d_ts = 10000  # 单样本时，硬编码给个 10ms 的周期

        # 这里容差取采样平均周期的 3/5 > 1/2, 保证尽可能进行时间同步:
        # 容差大了最坏的结果也就是按序列重写 sel 的时间戳(可能错开一个采样，有乱序的可能)，
        # 容差小的可能导致时间戳仅部分或者不进行同步
        tolerence_us = max(d_ts * 3 / 5, 6000)  # 最低 6ms 的容差

        # 将后面几组电机数据同步到第一组
        for x in range(1, len(motor_samples)):
            sel = motor_samples[x]
            i, j = 0, 0
            len1, len2 = len(ref), len(sel)
            while i < len1 and j < len2:
                if abs(ref[i].timestamp_us - sel[j].timestamp_us) < tolerence_us:
                    sel[j].timestamp_us = ref[i].timestamp_us
                    i += 1
                    j += 1
                elif ref[i].timestamp_us < sel[j].timestamp_us:
                    i += 1
                else:
                    j += 1

            # 稳一手, 强行纠正可能的乱序，保证同步后，sel 时间戳还是单调递增
            for idx in range(1, len2):
                sel[idx].timestamp_us = max(sel[idx].timestamp_us, sel[idx - 1].timestamp_us)

    def merge_samples_by_ts(
        self,
        samples_to: SamplesDeque,
        samples_from: monitor_pb2.SensorDataCollection,
    ):
        """向 samples_to 中追加 samples_from 中新增的采样数据(按时间戳)
        追加时，samples_to 通过 deque 限制缓存数据数量，万一点检时卡在那里了呢
        """
        for sensor in samples_from.DESCRIPTOR.fields_by_name:
            to_vec = getattr(samples_to, sensor)
            from_vec = getattr(samples_from, sensor)
            # 找最后的时间戳，复制时间戳大于这个的数据
            ts_ref = to_vec[-1].timestamp_us if to_vec else 0
            to_vec.extend(x for x in from_vec if x.timestamp_us > ts_ref)

    def filter_samples_by_ts(self, samples: monitor_pb2.SensorDataCollection):
        def get_filtered_data_for_sensor(sensor_id: SensorID, samples: Sequence) -> Sequence:
            if not samples:
                return []

            # 获取最近一个采样的时间戳，并更新时间戳记录
            ts_ref = self._last_samples_ts.get(sensor_id, 0)
            self._last_samples_ts[sensor_id] = max(samples[-1].timestamp_us, ts_ref)

            for i, v in enumerate(samples):
                if v.timestamp_us > ts_ref:
                    return samples[i:]
            return []

        for sensor_id, field_name in SENSOR_ID_TO_SAMPLES_FIELD.items():
            # 注意 clear 前后需要保存和重新取对象引用
            sensor_samples = getattr(samples, field_name)
            filtered_samples = get_filtered_data_for_sensor(sensor_id, sensor_samples)
            samples.ClearField(field_name)
            sensor_samples = getattr(samples, field_name)
            sensor_samples.extend(filtered_samples)

    def queue_process_samples(self, *args, **kwargs):
        self.executor.submit(self.process_samples, *args, **kwargs)

    @MiscUtils.skip_if_running
    def process_samples(
        self, samples: monitor_pb2.SensorDataCollection, spec: ReportTaskSpec, on_critical=None
    ):
        """处理采样数据，生成告警列表，并对告警项进行上报

        1. 一个采样周期，对于单一告警项只上报一次告警
        2. 点检开始时，收到的采样数据合并到点检采样集合
        3. 点检结束后，开始检查点检采样集合，处理点检上报
        """

        # 同步电机采样数据时间
        self.sync_motor_sample_time(samples)

        # 过滤已经检查过的旧采样数据
        self.filter_samples_by_ts(samples)

        # 将新拿到的采样数据合并到采样记录
        if self._inspection_enabled:
            self.merge_samples_by_ts(samples_to=self._queued_samples, samples_from=samples)

        # 检查前清除告警
        self._alerts.clear()

        # 检查这轮的采样: 震动，噪音，载荷
        self.check_vibration(SensorID.Vibration_1, samples.vibration_1)
        self.check_noise(SensorID.Noise_1, samples.noise_1)
        self.check_loadunit(SensorID.LoadUnit_1, samples.loadunit_1)

        # 处理电机数据
        for sensor_id, field_name in SENSOR_ID_TO_SAMPLES_FIELD.items():
            if not field_name.startswith('motor_'):
                continue
            senspr_samples = getattr(samples, field_name)
            self.check_motor(sensor_id, senspr_samples)

        # 有任何告警超过限制先回调处理
        if on_critical and any(x.level == AlertLevel.CRITICAL for x in self._alerts.values()):
            on_critical()

        # 执行告警上报，然后清除告警记录
        for alert in self._alerts.values():
            self.report_alert(alert, spec)
        self._alerts.clear()

        # 检查是否点检结束，这里点检检查生成的告警不会上报
        if self._check_inspection_on_this_sample:
            if not self._spec_for_inspection:
                _logger.error('inspection spec not provided!')
            else:
                # 根据动作类型获取要需要的电机检查类型
                check_types = {
                    x
                    for action in self._inspection_check_actions
                    for x in action.get_check_types()
                    if x.get_motor_type() != 'steering'  # 暂不包含转向电机
                }
                # 使用最后一个 action
                check_action = self._inspection_check_actions[-1]
                # 遍历检查列表，执行检查上报
                for check_type in check_types:
                    check_spec = self._spec_for_inspection.model_copy(deep=True)
                    check_spec.check_type = check_type
                    check_spec.check_action = check_action
                    spec_to_report = self.check_inspection_samples(check_spec)
                    if spec_to_report:
                        self.report_inspection_result(spec_to_report)
                    self._alerts.clear()

            self._check_inspection_on_this_sample = False
            self._spec_for_inspection = None
            self._queued_samples = SamplesDeque()

    def report_alert(self, alert: SensorAlert, spec: ReportTaskSpec):
        service = ReportService()

        _logger.warning(f'report alert: {alert.sensor_id.name} ..')

        # 因为会有不同告警，这份共用的 spec 信息需要复制出来
        spec_this = spec.model_copy(deep=True)
        # 默认告警任务设置
        spec_this.uniformID = alert.uniform_id
        # 告警允许两种模式：一次性告警，时段告警（时间内无更新自动结束）
        if not spec_this.end_on_collect and not spec_this.end_at_timestamp:
            # 如果都未设置，就强制一次性告警
            spec_this.end_on_collect = True

        # 填充告警信息
        assert spec_this.alarmData
        alarmdata = spec_this.alarmData
        alarmdata.mainTypeCode = f'{alert.sensor_id}'
        alarmdata.minorTypeCode = f'{alert.atype}'  # uniformID 作为告警分类信息上报
        alarmdata.beginDate = datetime.fromtimestamp(alert.timestamp_us / 1e6)
        alarmdata.alarmModule = '1'  # 设备告警

        # 采样平均值
        avg = alert.value

        # 按照告警类型继续填充告警信息
        if alert.atype == AlertType.OverloadWeight:
            alarmdata.parameter1 = f'{alert.value.weight_kg:.1f}kg'
            alarmdata.parameter2 = spec.carrier_code
        elif alert.atype == AlertType.OffsetLarge:
            alarmdata.parameter1 = f'{alert.value.offset_m * 1000:.1f}mm'  # mm 上报
            alarmdata.parameter2 = f'{math.degrees(alert.value.angle_rad):.1f}rad'  # 角度值上报
        elif alert.atype == AlertType.Noise:
            alarmdata.parameter1 = f'{avg.noise_db:.1f}dB'
        elif alert.atype == AlertType.Vibration:
            alarmdata.parameter1 = json.dumps(
                [int(x * 1000) for x in (avg.x_ac_g, avg.y_ac_g, avg.z_ac_g)]
            )
        elif alert.atype == AlertType.MotorCurrent:
            alarmdata.parameter1 = f'{avg.current_A:.3f}A'
            # 仅对举升电机上报货架码
            if alert.sensor_id == SensorID.MotorLift:
                alarmdata.parameter2 = spec.carrier_code
        elif alert.atype == AlertType.SN_Invalid:
            # 声明要求上传扫码图片，图片加载延迟到上报时
            spec_this.upload_img = True

        service.add_task(
            task=ReportTask(
                name=alert.sensor_id.name,
                reporter_type=ReportType.AgvAlarm,
                spec=spec_this,
                interval_ms=900,
            )
        )

    def check_inspection_samples(self, spec: ReportTaskSpec) -> Optional[ReportTaskSpec]:
        """按照点检任务 spec 声明的 check_type 处理点检采样缓存"""

        # 复制一份 spec, 使用 check_type 作为 uniformID
        spec = spec.model_copy(deep=True)
        spec.uniformID = hash(spec.check_type)

        # 生成一个 checkdata
        if not spec.checkDatas:
            spec.checkDatas = [AutoCheckData()]
        check_data = spec.checkDatas[0]

        # 填充起始时间
        if self._inspection_begin_time:
            dt = datetime.now() - self._inspection_begin_time
            check_data.message.processDuration = dt.total_seconds()
            check_data.message.creatTime = self._inspection_begin_time

        # 按点检类型填充采样数据
        motor_type = spec.check_type.get_motor_type()
        if motor_type:

            def fill_motor_message(motor_id, samples, name):
                # 检查数据，有问题就生成 alert 告警
                self.check_motor(motor_id, samples)
                msg = check_data.message
                setattr(msg, f'{name}Current', [{x.timestamp_us: x.current_A} for x in samples])
                setattr(msg, f'{name}Rpm', [{x.timestamp_us: x.speed_rpm} for x in samples])
                setattr(msg, f'{name}Temp', [{x.timestamp_us: x.temperature_C} for x in samples])

            if motor_type == 'lift':
                fill_motor_message(SensorID.MotorLift, self._queued_samples.motor_lift, 'lift')
            elif motor_type == 'propel':
                fill_motor_message(SensorID.MotorLeft, self._queued_samples.motor_left, 'left')
                fill_motor_message(SensorID.MotorRight, self._queued_samples.motor_right, 'right')
            elif motor_type == 'steering':
                spec.check_result = AutoCheckResult.Fail
                spec.err_msg = '此机型未配置转向电机'
            else:
                spec.check_result = AutoCheckResult.Fail
                spec.err_msg = f'未定义的 motor_type：{motor_type}'

        elif spec.check_type.is_vibration_check():
            samples = self._queued_samples.vibration_1
            self.check_vibration(SensorID.Vibration_1, samples)
            detail = VibrationDetail(action=spec.check_action.value)
            detail.vibrationData.x = [v.x_ac_g for v in samples]
            detail.vibrationData.y = [v.y_ac_g for v in samples]
            detail.vibrationData.z = [v.z_ac_g for v in samples]
            detail.dataFrequency = round(self.get_freq_by_ts(samples))
            check_data.message.checkDetails = [detail]

        elif spec.check_type.is_noise_check():
            samples = self._queued_samples.noise_1
            self.check_noise(SensorID.Noise_1, samples)
            detail = NoiseDetail(action=spec.check_action.value)
            detail.noiseData.extend({x.timestamp_us: x.noise_db} for x in samples)
            check_data.message.checkDetails = [detail]
        else:
            spec.check_result = AutoCheckResult.Fail
            spec.err_msg = f'未定义的 check_type: {spec.check_type}'

        return spec

    def report_inspection_result(self, spec: ReportTaskSpec):
        """生成并添加点检数据上报任务，数据来自 spec"""

        _logger.info(f'report on check_type: {spec.check_type} ..')

        # 叠加这里的点检数据检查，如果有出现告警项，认为点检失败
        if self._alerts:
            spec.check_result = AutoCheckResult.Fail
            if not spec.err_msg:  # 如果没有设置失败信息，就从告警里随便找一条
                for alert in self._alerts.values():
                    if alert.message:
                        spec.err_msg = alert.message
                        break

        service = ReportService()
        service.add_task(
            task=ReportTask(
                name=f'{spec.check_action.value}.{spec.check_type.name}',
                reporter_type=ReportType.AgvAutoCheck,
                spec=spec,
                max_count=1,  # 上报一次后退出
                interval_ms=500,  # 配合 5s 退出时间, 可以重试 10 次
                end_time=service.get_loop_ts() + 5,  # 5s 后即使失败也退出
            )
        )

    def queue_alert(self, alert: SensorAlert):
        """添加告警消息，告警等级相同时始终更新，等级不同时保持高等级"""
        alert_queued = self._alerts.get(alert.uniform_id)
        if not alert_queued or alert.level in (alert_queued.level, AlertLevel.CRITICAL):
            self._alerts[alert.uniform_id] = alert
