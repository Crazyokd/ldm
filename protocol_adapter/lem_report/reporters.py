import logging

from protocol_adapter.lem_report.models_payload import AlarmModel, AutoCheckModel
from protocol_adapter.lem_report.models import ControlState, ReportPayload, ReportType
from protocol_adapter.lem_report.reporter import BaseReporter

logger = logging.getLogger(__name__)


class SensorMonitor(BaseReporter):
    """
    SensorMonitor: 周期主动从 sros 拿缓存的采样数据
    收到 protobuf 返回的数据后，交给 SensorProcessor 回调处理
    """

    def _collect_data(self):
        # 调用回调，发送传感器采用请求
        assert self.task.callback
        self.task.callback()

    def _build_payload(self, data: None) -> ReportPayload:
        # 不上报，仅执行回调
        return ReportPayload(skip=True)


class AlarmReporter(BaseReporter):
    MSG_TAG = 'AGV_ALARM_INFO'

    def _collect_data(self):
        spec = self.task.spec

        if not spec.alarmData:
            raise AssertionError('alarmData not provided')

        # 从 spec 同步信息到 alarmData
        if not spec.alarmData.deviceNo:
            spec.alarmData.deviceNo = str(spec.agv_id)
        if not spec.alarmData.mapCode:
            spec.alarmData.mapCode = spec.map_code
        if not spec.alarmData.alarmGuid:
            spec.alarmData.alarmGuid = spec.guid

        # 加载图片
        if spec.upload_img:
            spec.alarmData.imageData = ''
            img_path = self.find_image_around_the_time(directory='/sros/log/data')
            if img_path:
                spec.alarmData.imageData = self.encode_image(img_path)

    def _build_payload(self, data: None) -> ReportPayload:
        # 更新请求 id 和请求时间
        assert self.task.req_info
        self.task.req_info.reqCode = self.gen_req_code()
        self.task.req_info.reqTime = self.get_cur_time()

        # 上报控制
        skip_this = False
        control_state = ControlState.Continue

        # 通过 spec 传递告警信息
        spec = self.task.spec
        assert spec.alarmData

        # 跳过本次上报：
        # 1. 需要上传图片的，但没找到图片跳过
        # 2. 告警已经上报过（目前告警通过reload更新上报信息，未更新时不必重新上报）
        if (spec.upload_img and not spec.alarmData.imageData) or spec.count_send > 0:
            skip_this = True

        # 主动结束上报的情况:
        # 1. 只进行一次性上报的（采集一次就结束，上报一次）
        # 2. 等待结束周期内，如果没有告警更新，就主动结束此次告警
        if not spec.alarmData.endDate and spec.end_on_collect:
            spec.alarmData.endDate = self.get_cur_time()
            control_state = ControlState.Stop
        if spec.end_at_timestamp and self.get_loop_ts() > spec.end_at_timestamp:
            spec.alarmData.endDate = self.get_cur_time()
            spec.alarmData.parameter1 = ''
            spec.alarmData.parameter2 = ''
            control_state = ControlState.Stop
            # 超时后主动结束的结束报文，会被标记跳过，这里要取消跳过
            if spec.count_send == 1:
                skip_this = False

        model = AlarmModel.model_validate(self.task.req_info.model_dump())
        model.data.append(spec.alarmData)

        return ReportPayload(
            value=model.model_dump(exclude_none=True), state=control_state, skip=skip_this
        )


class AutoCheckReporter(BaseReporter):
    MSG_TAG = 'AGV_AUTO_CHECK_RESULTS'

    def _collect_data(self):
        spec = self.task.spec

        if not spec.checkDatas:
            raise AssertionError('checkData not provided')

        # 从 spec 同步信息到 alarmData
        for checkData in spec.checkDatas:
            if not checkData.deviceNo:
                checkData.deviceNo = str(spec.agv_id)
            if not checkData.mapCode:
                checkData.mapCode = spec.map_code
            if not checkData.commandId:
                checkData.commandId = spec.command_id
            if not checkData.checkType:
                checkData.checkType = str(spec.check_type)
            if not checkData.message.motorType:
                checkData.message.motorType = spec.check_type.get_motor_type() or None

            checkData.message.autoCheckResult = spec.check_result.value
            if spec.err_msg:
                logger.warning(f'set errMsg: {spec.err_msg}')
                checkData.message.errMsg = spec.err_msg

    def _build_payload(self, data: None) -> ReportPayload:
        # 更新请求 id 和请求时间
        assert self.task.req_info
        self.task.req_info.reqCode = self.gen_req_code()
        self.task.req_info.reqTime = self.get_cur_time()

        # 上报控制，点检结果正常只上报一次，这里默认继续，任务需要设置 max_count=1
        control_state = ControlState.Continue
        skip_this = False

        # 通过 spec 传递告警信息
        spec = self.task.spec
        assert spec.checkDatas

        model = AutoCheckModel.model_validate(self.task.req_info.model_dump())
        model.data.extend(spec.checkDatas)

        return ReportPayload(
            value=model.model_dump(exclude_none=True), state=control_state, skip=skip_this
        )


class StatusReporter(BaseReporter):
    MSG_TAG = 'AGV_DEVICE_STATUS'


class MeasureReporter(BaseReporter):
    MSG_TAG = 'AGV_MEASURE_INFO'


class ChargeStationStatusReporter(BaseReporter):
    MSG_TAG = 'CDZ_DEVICE_STATUS'


class ChargeStationAlarmReporter(BaseReporter):
    MSG_TAG = 'CDZ_ALARM_INFO'


class ChargeStationTaskReporter(BaseReporter):
    MSG_TAG = 'CDZ_TASK_INFO'


MAP_REPORTER_TYPE_TO_CLASS = {
    ReportType.SensorMonitor: SensorMonitor,
    ReportType.AgvStatus: StatusReporter,
    ReportType.AgvAlarm: AlarmReporter,
    ReportType.AgvMeasure: MeasureReporter,
    ReportType.AgvAutoCheck: AutoCheckReporter,
    ReportType.ChargeStationStatus: ChargeStationStatusReporter,
    ReportType.ChargeStationAlarm: ChargeStationAlarmReporter,
    ReportType.ChargeStationTask: ChargeStationTaskReporter,
}
