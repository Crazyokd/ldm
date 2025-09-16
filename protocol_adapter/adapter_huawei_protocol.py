import contextlib
import logging
import time
from threading import Timer
from collections import deque

from protocol_adapter.config import Config
from protocol_adapter.lem_report.sensor_processor import (
    AlertLevel,
    AlertType,
    SensorID,
    SensorAlert,
    SensorProcessor,
)
from protocol_adapter.lem_report.models import ReportTask, ReportTaskSpec, ReportType
from protocol_adapter.lem_report.models_payload import AlarmData
from protocol_adapter.lem_report.service import ReportService
from protocol_adapter.models.task import TaskState, TaskType, TaskItem
from protocol_adapter.models.state import SystemState
from protocol_adapter.models.maps import ActionErrorCode_To_SyetemState
from protocol_adapter.loop_timer import LoopTimer
from protocol_adapter.server_wrapper import ServerWrapper
from protocol_adapter.srp_wrapper import SrpWrapper
from protocol_adapter.data_parser import DMCodeParser
from protocol_adapter.execute_task import ExecuteTask
from protocol_adapter.const import DeviceType, ConfigKey

from protocol_adapter.protobuf_wrapper import main_pb2, monitor_pb2
from protocol_adapter.huawei_model.const import *
from protocol_adapter.huawei_model.const import (
    DetectType,
    ShelfTaskState,
    ChargeMaintain,
    get_int_dat,
)

from protocol_adapter.huawei_protocol import HuaweiProtocol
from protocol_adapter.utils import AngleUtils, GeometryUtils, MiscUtils

_logger = logging.getLogger(__name__)


def check_and_init_server_wrapper_server(func):
    def wrapper(self, *args, **kwargs):
        if self._server_wrapper._server is None:
            data = self._srp_wrapper.get_sros_configs([ConfigKey.SERVER_IP, ConfigKey.SERVER_PORT])
            self._server_wrapper.set_server(
                (data[ConfigKey.SERVER_IP], data[ConfigKey.SERVER_PORT])
            )
        return func(self, *args, **kwargs)

    return wrapper


DELAY_IDLE_FOR_RISK_ACTION_CT = 10
UPLOAD_FINISHED_ON_TASK_DONE_CT = 10
STAY_BUSY_ON_TASK_SWITCH_CT = 10

# 传感器采样数据读取的周期
SENSOR_SAMPLE_INTERVAL_MS = 1000
# 点检任务周期时间
AUTOCHECK_INTERVAL_S = 24 * 3600
# 启动后点检延迟时间
DELAY_AUTOCHECK_ON_INIT_S = 6 * 60


class HuaweiProtocolAdapter:
    def __init__(self, srp: SrpWrapper, config: Config):
        _logger.info('Create huawei protocol adapter')

        self._cnt = 0

        self._srp_wrapper = srp
        self._srp_wrapper.add_charge_finish_callback(self.on_charge_finish)
        # 不需要小车自检电量低时申请充电，充电动作有调度系统下发，小车只要执行充电任务
        # self._srp_wrapper.add_low_battery_callback(self.on_low_battery)
        self._srp_wrapper.add_brake_switch_changed_callback(self.on_brake_sw_changed)
        self._srp_wrapper.add_emergency_state_changed_callback(self.on_emergency_state_changed)
        self._srp_wrapper.add_dmcode_changed_callback(self.check_dmcode_changed)
        self._srp_wrapper.add_map_changed_callback(self.check_map_changed)
        self._srp_wrapper.add_callbacks_sensor_samples(self.on_sensor_samples)

        self._config = config
        self._server_wrapper = ServerWrapper(self.receive_data, self.receive_data_from_alarm_server)
        self._protocol = HuaweiProtocol()
        self._report_service: ReportService

        self._task_thread = ExecuteTask(
            self._config, self._srp_wrapper, self._server_wrapper, self._protocol, self
        )

        self._cur_execute_task = None  # 当前正在执行的任务
        self._cur_task_id = 0  # 保持上一次的任务ID
        self._cur_sub_task_id = 0
        self._cur_pause_task = None
        self._cur_release_task_id = 0
        self._cur_release_sub_task_id = -1
        self._task_to_switch = None  # 记录要切换到的任务
        self.last_fault_list = []

        self._reconnecting = False
        self._lost_conn_timer = None  # 掉线定时器
        self._upload_status_timer = None  # 上传状态定时器
        self._upload_battery_status_timer = None  # 上传电池状态定时器
        self._release_timer = None
        self._release_reset_timer = None

        self._dm_code_type = ''  # 地码类型，对应地图名
        self._dm_code_type_detect = ''  # 下视扫到的地码,上报的优先级最低
        self._dm_code_type_ldm = ''  # ldm设置地图时下发地码,上报优先级最高
        self._dm_code_type_map = ''  # 当前地图映射的地码,上报优先级第二

        self._code_sn = ''
        self._map_name = ''

        self._loop_timer = None
        self._brake_delay_timer = None

        # 顶升后，上视摄像头会被关闭，顶升过程中都需要上报此货架id，所以此处缓存一下
        self._shelf_id = ''
        # 顶升状态下重启sros后会丢失掉载货状态和货码信息，货架仍处于顶升状态
        self._check_load_ok = False
        self._ignore_count = 0
        self._pre_action_no = -1
        self._release_state = 0  # 0:NONE 1:wait_for_runnig 2:runnig
        self._idle_delay_ct = 0  # 风险任务延迟上报 IDLE
        self._finished_ct = 0  # 任务完成后，上报完成状态计数
        self._busy_switch_ct = 0  # 切换任务时报 BUSY 的计数

        self._is_running = True

        # 记录最近几次状态切换
        self._latest_states = deque(maxlen=12)
        self._latest_actions = deque(maxlen=10)

    def start(self):
        self.fetch_config()

        # 同步配置信息后再启动上报服务
        report_settings = self._config.report_settings
        self._report_service = ReportService(config=report_settings)
        self._report_service.start(wait_ready=True)

        # 配置初始化加载后才能启动 server_wrapper: 数据处理的回调依赖配置中的 server ip
        self._server_wrapper.start(local_port=self._config.local_port)

        # 发送注册请求
        self.request_register()
        self.reset_lost_conn_timer()

        # 添加传感器采样任务
        self.add_sensor_sample_task()

    def stop(self):
        self._is_running = False

        def stop_timer(timer):
            if timer is not None:
                timer.cancel()

        stop_timer(self._lost_conn_timer)
        stop_timer(self._upload_status_timer)
        stop_timer(self._upload_battery_status_timer)
        stop_timer(self._loop_timer)

        self._task_thread.stop()
        self._server_wrapper.stop()
        self._report_service.stop()

    def add_sensor_sample_task(self):
        """添加周期传感器监控任务
        (这个函数最多只能执行一次)

        1. 采样数据获取任务
        2. 检查触发点检逻辑
        """

        # 保存回调的状态，集中管理单独逻辑的相关状态
        class AutoCheckContext:
            enabled = False
            next_check_time: float = 0  # 下次点检时间
            enable_time: float = 0  # 点检启用时间
            mark_start = False
            mark_stop = False

        ctx = AutoCheckContext
        processor = SensorProcessor()

        def enable_inspection():
            """启用点检，但具体什么时候启用还得看系统状态"""
            _logger.info('inspection wait start ..')
            ctx.enabled = True
            ctx.enable_time = time.time()
            ctx.mark_start = False
            ctx.mark_stop = False

        def stop_inspection():
            _logger.info('inspection stop')
            ctx.enabled = False

            processor.set_inspection_state(
                enable=False,
                spec=ReportTaskSpec(
                    agv_id=self.get_robot_id(),
                    carrier_code=self._task_thread.get_detect_shelf_sn(),
                    map_code=self._srp_wrapper.get_location_map_name(),
                    command_id=f'{self._cur_task_id}',
                ),
                check_actions=self._latest_actions.copy(),
            )
            self._latest_states.clear()
            self._latest_actions.clear()

            # 关闭噪音录制
            self._task_thread.do_async_action(141, 1, 0)

        def on_inspection_enabled():
            # 开启自检两秒内不进行标记
            if time.time() < ctx.enable_time + 2:
                self._latest_states.clear()
                self._latest_actions.clear()
                return

            # 检查点检停止条件
            start_set = (
                SystemState.BUSY,
                SystemState.EXECUTE_ACTION,
                SystemState.ARC_MOVE,
                SystemState.AUTO_ADJUST,
            )
            stop_set = (
                SystemState.IDLE,
                SystemState.TASK_FINISH,
            )

            for state in self._latest_states.copy():
                if not ctx.mark_start and state in start_set:
                    _logger.info('inspection mark start')
                    ctx.mark_start = True
                    self._latest_states.clear()  # 标记启动后清空，防止之前的 idle 导致错误标记结束

                    # 启用噪音记录(可能需要等待当前任务结束后)
                    self._task_thread.do_async_action(141, 1, -1)

                    # 在检测到任务开始后，才真正启用自检采样处理
                    processor.set_inspection_state(enable=True)
                    break
                elif ctx.mark_start and not ctx.mark_stop and state in stop_set:
                    _logger.info('inspection mark stop')
                    ctx.mark_stop = True
                    break

            if ctx.mark_stop and len(self._latest_actions) > 0:
                stop_inspection()

        def sample_monitor():
            # 周期拿新增传感器采样数据
            self._srp_wrapper.fetch_sensor_samples()

            # 处理本地周期点检
            current_ts = time.time()

            # 检查设置启动点检时间
            if ctx.next_check_time == 0:
                ctx.next_check_time = current_ts + DELAY_AUTOCHECK_ON_INIT_S

            # 到了点检时间
            if current_ts > ctx.next_check_time:
                ctx.next_check_time += AUTOCHECK_INTERVAL_S
                enable_inspection()

            # 点检运行中的检查结束条件
            if ctx.enabled:
                on_inspection_enabled()

        task = ReportTask(
            name='fetch_samples',
            reporter_type=ReportType.SensorMonitor,
            interval_ms=SENSOR_SAMPLE_INTERVAL_MS,
            callback=sample_monitor,
            enable_debug=False,
            spec=ReportTaskSpec(
                agv_id=self.get_robot_id(),
                delay_ms=500,  # 延迟启动
            ),
        )
        self._report_service.add_task(task)

    def fetch_config(self):
        _logger.info('fetch and sync config ..')

        keys = [
            ConfigKey.SERVER_IP,
            ConfigKey.SERVER_PORT,
            ConfigKey.NICKNAME,
            ConfigKey.AGV_MODEL,
            ConfigKey.ACTUATOR_TYPE,
            ConfigKey.RACK_WIDTH,
            ConfigKey.RACK_LENGTH,
            ConfigKey.STOP_DISTANCE,
            ConfigKey.STOP_DISTANCE_BACKWARD,
            ConfigKey.STOP_WIDTH_OFFSET,
            ConfigKey.SLOW_DISTANCE,
            ConfigKey.SLOW_WIDTH_OFFSET,
        ]
        sros_config = {}
        for _ in range(0, 20):
            try:
                sros_config = self._srp_wrapper.get_sros_configs(keys)
                break
            except BaseException as e:
                _logger.info(f'get config error: {e}')
                time.sleep(1)

        for key in keys:
            if sros_config.get(key) in (None, 'NA'):
                _logger.error(f'fetch sros config: `{key}` no define')
                return

        _logger.info('sync config fetched from srp')
        self._config.sync_from_config_data(sros_config)

        endpoint = (self._config.server_ip, self._config.server_port)
        _logger.info(f'set server endpoint: {endpoint}')
        self._server_wrapper.set_server(endpoint)

    def do_recv_dat_from_server(self, dat):
        ba_header = dat[:MSG_HEADER_LEN]
        ba_body = dat[MSG_HEADER_LEN:]
        header = self._protocol.unpack_header(ba_header)
        msg_type = header['type']
        msg_sn = header['sn']
        try:
            if msg_type == MSG_RSP_REGISTER:
                self.process_register_rsp(ba_body)
                if self.get_device_state() == SystemState.PAUSE:
                    with contextlib.suppress(Exception):
                        self._srp_wrapper.cancel_movement_task()
                    self._task_thread.cancel_task(False)
                    self._cur_execute_task = None
            elif msg_type == MSG_REQ_DEVICE_ABILITY:
                self.process_device_ability_req(msg_sn)
            elif msg_type == MSG_REQ_CFG_UPLOAD_STATUS:
                self.process_cfg_upload_status_req(msg_sn, ba_body)
            elif msg_type == MSG_REQ_CFG_WARN_SERVER:
                self.process_cfg_warning_server_req(msg_sn, ba_body)
            elif msg_type == MSG_REQ_CFG_TIME_SYNC:
                self.process_cfg_time_sync_req(msg_sn, ba_body)
            elif msg_type == MSG_REQ_CFG_GLOBAL_PRECISION:
                self.process_cfg_global_precision(msg_sn, ba_body)
            elif msg_type == MSG_REQ_CFG_TIMEOUT:
                self.process_cfg_timeout(msg_sn, ba_body)
            elif msg_type == MSG_REQ_CFG_MOVEMENT_PARAM:
                self._protocol.unpack_cfg_movement(ba_body)
                rsp = self._protocol.pack_common_rsp(
                    self.get_robot_id(), msg_sn, MSG_RSP_CFG_MOVEMENT_PARAM
                )
                self.send_response(rsp)
            elif msg_type == MSG_REQ_CFG_UPLOAD_BATTERY:
                self.process_cfg_upload_battery(msg_sn, ba_body)
            elif msg_type == MSG_REQ_CFG_CAPACITY_SET:
                allow_dispatch_task_ahead, is_need_lock_space = self._protocol.unpack_cfg_capacity(
                    ba_body
                )
                _logger.info(
                    'Receive cfg capacity set: allow_dispatch_task_ahead->'
                    + str(allow_dispatch_task_ahead)
                    + ' is_need_lock_space->'
                    + str(is_need_lock_space)
                )
                # TODO 该配置暂时未使用
                self._config.set_allow_dispatch_task_ahead(allow_dispatch_task_ahead)
                self._config.set_is_need_lock_space(is_need_lock_space)
                rsp = self._protocol.pack_common_rsp(
                    self.get_robot_id(), msg_sn, MSG_RSP_CFG_CAPACITY_SET
                )
                self.send_response(rsp)
            elif msg_type == MSG_RSP_UPLOAD_STATE:
                self.reset_lost_conn_timer()
                if self._reconnecting:
                    self._reconnecting = False
                    self.send_alarm(
                        ALARM_CATEGORY_1,
                        ALARM_CODE_LOST_CONNECT,
                        ALARM_STATUS_OFF,
                        ALARM_GRADE_ERROR,
                    )
            elif msg_type == MSG_RSP_REPLAN_ONLINE:
                resp = self._protocol.unpack_replan_online(ba_body)
                _logger.info(f'get replan online resp: {resp}')
            elif msg_type == MSG_RSP_LOCK_SPACE:
                self._task_thread.process_lock_space_rsp(ba_body)
            elif msg_type == MSG_RSP_UNLOCK_SPACE:
                self._task_thread.process_unlock_space_rsp(ba_body)
            # 单独举升货架任务/举升货架叠加直线(弧线)运动/空车直线(弧线)移动任务
            elif msg_type in (
                MSG_REQ_RAISE_SHELF,
                MSG_REQ_PUT_SHELF,
                MSG_REQ_ROLLER_CTRL,
                MSG_REQ_LINEAR_MOVE_AFTER_RAISE_SHELF,
                MSG_REQ_LINEAR_MOVE_AFTER_PUT_SHELF,
                MSG_REQ_NO_PAYLOAD_ARC_MOVE,
                MSG_REQ_ARC_MOVE_AFTER_RAISE_SHELF,
                MSG_REQ_ARC_MOVE_AFTER_PUT_SHELF,
                MSG_REQ_CHARGE,
                MSG_REQ_SLAM_NAV,
                MSG_REQ_NO_PAYLOAD_LINEAR_MOVE,
                MSG_REQ_DETECT_CTRL,
                MSG_REQ_LINEAR_NO_PAYLOAD_MULTI_PATH_MOVE,
                MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF,
                MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_PUT_SHELF,
                MSG_REQ_ARM_FORK_LOAD_ACTION,
                MSG_REQ_ARM_FORK_UNLOAD_ACTION,
                MSG_REQ_SMT_MULTI_PATH_MOVE,
                MSG_REQ_SMT_LOAD_ACTION,
                MSG_REQ_SMT_UNLOAD_ACTION,
            ):
                self._task_thread.changed_map_response = True
                self._task_to_switch = None
                self.process_move_req(msg_sn=msg_sn, type_code=msg_type, dat=ba_body)
            elif msg_type == MSG_REQ_PAUSE:
                task = self._protocol.unpack_command_req(ba_body, MSG_REQ_PAUSE)
                _logger.info(f'Pause task {task.get_task_id_str()}')
                self.response_common_cmd(msg_sn=msg_sn, type_code=MSG_RSP_PAUSE)
                self._srp_wrapper.pause_task()
                self.process_command_task(MSG_REQ_PAUSE, ba_body)
            elif msg_type == MSG_REQ_CONTINUE:
                self._task_thread.changed_map_response = True
                task = self._protocol.unpack_command_req(ba_body, MSG_REQ_CONTINUE)
                _logger.info(f'Continue task {task.get_task_id_str()}')
                self.response_common_cmd(msg_sn=msg_sn, type_code=MSG_RSP_CONTINUE)
                # NOTE: 滚筒无料对接超时后，异常处理需要继续
                if self.get_device_state() != SystemState.PAUSE:
                    _logger.warning('continue without Pause')
                with contextlib.suppress(Exception):
                    self._srp_wrapper.continue_task()
                self.process_command_task(MSG_REQ_CONTINUE, ba_body)
            elif msg_type == MSG_REQ_CANCEL:
                task = self._protocol.unpack_command_req(ba_body, MSG_REQ_CANCEL)
                _logger.info(f'Cancel task {task.get_task_id_str()}')
                self.response_common_cmd(msg_sn=msg_sn, type_code=MSG_RSP_CANCEL)
                if self._srp_wrapper.is_charging():
                    self._task_thread.stop_charge()
                else:
                    self._srp_wrapper.cancel_task()
                self.reset_task_state()
                self._task_thread.cancel_task()
                self.process_command_task(MSG_REQ_CANCEL, ba_body)
            elif msg_type == MSG_REQ_STOP_MOVE:
                task = self._protocol.unpack_command_req(ba_body, MSG_REQ_STOP_MOVE)
                _logger.info(f'Stop movement task {task.get_task_id_str()}')
                self.response_common_cmd(msg_sn=msg_sn, type_code=MSG_RSP_STOP_MOVE)

                if not self.is_system_state_idle():
                    try:
                        self._srp_wrapper.cancel_movement_task(True)
                    except Exception as e:
                        _logger.error(f'exception on cancel_movement_task: {e}')
                    self._task_thread.cancel_task(need_put_self=False)
                self.process_command_task(MSG_REQ_STOP_MOVE, ba_body)
            elif msg_type == MSG_RSP_CHARGE_MAINTAIN:
                if self._loop_timer:
                    self._loop_timer.cancel()
            elif msg_type == MSG_REQ_VERSIONS:
                _logger.info('Request versions')
                self.response_common_cmd(msg_sn=msg_sn, type_code=MSG_RSP_VERSIONS)
                self.upload_system_versions()
            elif msg_type == MSG_REQ_CHANGE_MAP:
                self.process_change_map(msg_sn=msg_sn, dat=ba_body)
            elif msg_type == MSG_REQ_SWITCH_NAV_MODE:
                self.process_changed_switch(msg_sn=msg_sn, dat=ba_body)
            elif msg_type == MSG_REQ_CFG_UPLOAD_DMCODE:
                self.response_common_cmd(msg_sn, MSG_RSP_CFG_UPLOAD_DMCODE)
                is_upload = self._protocol.unpack_cfg_upload_dmcode(ba_body)
                _logger.info(f'Request upload dmcode from server: {is_upload}')
                self._config.set_upload_dmcode_status(is_upload)
            elif msg_type == MSG_REQ_SHELF_ACTION_FORCE:
                self.response_common_cmd(msg_sn, MSG_RSP_SHELF_ACTION_FORCE)
                if not self._config.is_device_riser_rotate():
                    _logger.error('Not riser-rotate car receive force shelf actions')
                    return
                action_type, height = self._protocol.unpack_force_shelf_action(ba_body)
                _logger.info(f'Receive force action from server: {action_type} {height}')
                self._task_thread.force_shelf_action(action_type, height)
            elif msg_type == MSG_RSP_NOTIFY_MAP_CHANGE:
                _logger.info('Receive map changed notification response')
                self._task_thread.changed_map_response = True
            elif msg_type == MSG_RSP_UPLOAD_BATTERY_STATUS:
                _logger.info('Receive upload battery info notification response')
            elif msg_type == MSG_REQ_WAIT_RELEASE:
                _logger.info(f'Receive release command, body data: {ba_body.hex()}')
                self.response_common_cmd(msg_sn, MSG_RSP_WAIT_RELEASE)
                self.handle_release_msg(dat, ba_body)
            else:
                _logger.warning(f'Unsupport message type: {msg_type:#x}')
        except BaseException as e:
            _logger.error(f'Exception on: {msg_type:#x}')
            _logger.error(e, exc_info=True)

    def handle_release_msg(self, dat, ba_body):
        task_id = get_int_dat(ba_body, 4, 2, signed=False)
        sub_task_id = get_int_dat(ba_body, 6, 1, signed=False)

        _logger.info(f'release task_id {task_id}.{sub_task_id}')
        if self._cur_release_task_id == task_id and self._cur_release_sub_task_id == sub_task_id:
            _logger.info('ignore the same release task')
            return

        if self._srp_wrapper.is_emergency_state():
            _logger.info('ignore release task on emergency state')
            return

        _logger.info(f'get new release command, data: {dat.hex()}')
        self._cur_release_task_id = task_id
        self._cur_release_sub_task_id = sub_task_id

        release_timeout = get_int_dat(ba_body, 28, 4, signed=False)
        _logger.info(f'release timeout {release_timeout}s')
        release_timeout = max(release_timeout, 5)

        # 重置释放相关计时器，避免不同释放任务相互干扰
        self.reset_release_timers()
        self._release_timer = Timer(release_timeout, self.release_timeout_func)
        self._release_reset_timer = Timer(10, self.reset_timer_func)
        self._task_thread.do_async_action(131, 0, 79)
        self._release_timer.start()
        self._release_reset_timer.start()
        self._release_state = 1
        _logger.info('sent release action')

    def reset_release_timers(self):
        if self._release_timer:
            self._release_timer.cancel()
            self._release_timer = None
        if self._release_reset_timer:
            self._release_reset_timer.cancel()
            self._release_reset_timer = None

    def release_timeout_func(self):
        if self._release_state == 2:
            _logger.info('release timeout')
            self._srp_wrapper.cancel_task()
            self._release_state = 0
            self.reset_release_timers()

    def reset_timer_func(self):
        if self._release_state == 1:
            _logger.info('release too quick, not catch the state change')
            self._release_state = 0
            self.reset_release_timers()

    def get_robot_id(self) -> int:
        return self._config.get_robot_id()

    def on_charge_finish(self):
        _logger.info('on charge finish')
        self._task_thread.stop_charge()

    # 电量低时主动请求充电，RCS调度系统无该功能，
    # 只要实现系统让车去充电时，车能正常充电即可
    def on_low_battery(self, percent):
        # 如果已经在充电，则忽略
        if self._srp_wrapper.is_charging():
            return
        interval = self._config.get_msg_resend_interval()
        live_time = self._config.get_msg_live_time()
        self._loop_timer = LoopTimer(
            interval, self.request_charge_maintain, live_time, name='request_charge_maintain'
        )
        self._loop_timer.start()

    def on_emergency_state_changed(self, is_emergency):
        _logger.info(f'emergency state changed: {is_emergency}')
        if is_emergency:
            status = ALARM_STATUS_ON
        else:
            status = ALARM_STATUS_OFF

        self._srp_wrapper.fetch_system_state()
        # print(self._srp_wrapper.is_emergency_cause_by_hit())
        # if self._srp_wrapper.is_emergency_cause_by_hit():
        #     self.send_alarm(category=ALARM_CATEGORY_6, type_code=ALARM_CODE_HIT, status=ALARM_STATUS_PULSE, grade=ALARM_GRADE_HIGH)
        # else:
        self.send_alarm(
            category=ALARM_CATEGORY_7,
            type_code=ALARM_CODE_EMERGENCY,
            status=status,
            grade=ALARM_GRADE_HIGH,
        )

        if not is_emergency:
            self.check_and_update_thread_task_state_on_resume()

    def check_and_update_thread_task_state_on_resume(self):
        task = self._task_thread._cur_execute_task
        if not task:
            return

        # 通过急停恢复，将异常状态全部清掉，反正后面新任务有新检测
        task.state = TaskState.NONE

    # 解抱闸时会将任务状态复位，在任务出异常时可以方便快捷的恢复
    # 任务异常时，可以解抱闸后推动小车，解除抱闸后继续接收任务
    def on_brake_sw_changed(self, is_brake_on):
        # 解抱闸状态变化时，清空任务, 需要延时等电机正常，否则执行任务会报错
        _logger.info(f'on brake switch changed {is_brake_on}')

        try:
            self._srp_wrapper.cancel_task()  # 取消任务
        except BaseException as e:
            _logger.info(e)

        # 条件一直不满足
        # 恢复解抱闸后可以马上复位任务，由于判断了硬件故障状态，此时不会接收任务（仍会有电机故障）
        if is_brake_on == main_pb2.HardwareState.BreakSwitchState.BREAK_SW_OFF:
            self.reset_task_state()
            status = ALARM_STATUS_OFF
            # if self._brake_delay_timer:
            #     self._brake_delay_timer.cancel()
            #     self._brake_delay_timer = None
            # self._brake_delay_timer = Timer(15, self.do_brake_sw_changed, [is_brake_on])
            # self._brake_delay_timer.start()
        else:
            status = ALARM_STATUS_ON
        self.send_alarm(
            category=ALARM_CATEGORY_7,
            type_code=ALARM_CODE_EMERGENCY,
            status=status,
            grade=ALARM_GRADE_HIGH,
        )

    def do_brake_sw_changed(self, is_brake_on):
        self.reset_task_state()
        if is_brake_on == main_pb2.HardwareState.BREAK_SW_OFF:
            self.request_replan_online()
        self._brake_delay_timer = None

    def request_replan_online(self):
        _logger.info('send replan path request')
        dat = self._protocol.pack_replan_online_req(
            self.get_robot_id(), self._server_wrapper.get_msg_sn()
        )
        self.send_request(dat)

    def check_map_changed(self, map_name):
        if self._map_name != map_name:
            self.on_map_changed(map_name)

    def on_map_changed(self, map_name):
        _logger.info(f'map changed, new map is {map_name}')
        self._map_name = map_name
        if map_name not in ('', 'NO_MAP'):
            self._dm_code_type_map = self._config.get_dm_code_by_map(map_name)
            DMCodeParser.get_dmcode_list(map_name)

    def check_dmcode_changed(self, code_sn):
        if self._code_sn != code_sn:
            self.on_dmcode_changed(code_sn)

    def on_dmcode_changed(self, code_sn):
        self._task_thread.update_scurity_pose()
        self._code_sn = code_sn
        self._dm_code_type_detect = code_sn[6:8]
        _logger.info(f'dmcode sros detect {self._dm_code_type_detect}')
        if self._config.is_upload_dmcode():
            # 只要识别到地码有更新,与本地地图不一致才需要上报，当前底层尚未存在地码是否更新的判断
            if not DMCodeParser.is_dmcode_damaged(code_sn):
                _logger.info(f'dmcode is not damaged {code_sn}')
            dat = self._protocol.pack_upload_dmcode_req(
                self.get_robot_id(),
                self._server_wrapper.get_msg_sn(),
                self._srp_wrapper.get_cur_angle(),
                code_sn,
            )
            self.send_data(dat)
            _logger.info(f'upload dmcode: {code_sn}')

    def on_sensor_samples(self, sensor_samples: monitor_pb2.SensorDataCollection):
        pose = self._srp_wrapper.get_cur_pose()
        # 预填写此时告警相关的信息
        spec = ReportTaskSpec(
            agv_id=self.get_robot_id(),
            carrier_code=self._task_thread.get_detect_shelf_sn(),
            map_code=self._srp_wrapper.get_location_map_name(),
            alarmData=AlarmData(
                alarmX=pose['x'],
                alarmY=pose['y'],
            ),
            end_on_collect=True,  # 一次性告警，每个告警一个新的任务，上报后结束
        )

        def on_critical():
            _logger.warning('sample check on critical!')
            # self._srp_wrapper.pause_task()

        # 超出极限时暂停
        SensorProcessor().queue_process_samples(sensor_samples, spec, on_critical=on_critical)

    def reset_task_state(self):
        self.clear_current_task()
        self._task_thread.reset_task_state()

    def clear_current_task(self):
        _logger.info('clear_current_task')
        self._cur_execute_task = None

    @check_and_init_server_wrapper_server
    def send_request(self, dat):
        self._server_wrapper.send_request(dat)

    def send_response(self, dat):
        self.send_data(dat)

    def send_alarm(self, category, type_code, status, grade):
        _logger.info(f'send alarm: {category} {type_code} {status} {grade}')

        pose = self._srp_wrapper.get_cur_pose()
        dat = self._protocol.pack_alarm_request(
            device_id=self.get_robot_id(),
            msg_sn=self._server_wrapper.get_alarm_sn(),
            alarm_category=category,
            alarm_code=type_code,
            alarm_status=status,
            alarm_level=grade,
            x=pose['x'],
            y=pose['y'],
        )
        self._server_wrapper.send_alarm(dat)

        # 货架相关告警要另外给 LEM 写报告
        if type_code in (ALARM_CODE_SHELF_SN_MISMATCH, ALARM_CODE_NO_RECOGNIZE_SHELF_SN):
            service = ReportService()
            alert = SensorAlert(
                sensor_id=SensorID.SvcUp,
                level=AlertLevel.WARNING,
                atype=AlertType.SN_Invalid,
                value=None,
                timestamp_us=int(time.time() * 1e6),
                message='扫码未识别',
            )
            spec = ReportTaskSpec(
                agv_id=self.get_robot_id(),
                map_code=self._srp_wrapper.get_location_map_name(),
                alarmData=AlarmData(
                    alarmX=pose['x'],
                    alarmY=pose['y'],
                    parameter1=self._task_thread._last_shelf_sn,
                ),
                delay_ms=300,  # 延迟启动, 配合 uniformID 进行去重合并
                end_at_timestamp=service.get_loop_ts() + 2,  # 2s 无更新自动结束
            )
            SensorProcessor().report_alert(alert, spec)

    def get_state_to_override_for_some_case(self, dev_state: SystemState) -> SystemState:
        if dev_state != SystemState.IDLE:
            self._finished_ct = 0
            self._idle_delay_ct = 0
            self._busy_switch_ct = 0
            return dev_state

        # 任务完成后报几帧 SystemState.TASK_FINISH
        if self._cur_execute_task and self._cur_execute_task.state == TaskState.DONE:
            if self._finished_ct < UPLOAD_FINISHED_ON_TASK_DONE_CT:
                if self._finished_ct == 0:
                    _logger.info('set upload state: TASK_FINISH')
                self._finished_ct += 1
                return SystemState.TASK_FINISH
            else:
                self._finished_ct = 0
                self._cur_execute_task.state = TaskState.NONE
        else:
            self._finished_ct = 0

        # 风险动作延迟几帧报空闲
        if (
            self._cur_execute_task
            and self._cur_execute_task.is_task_type_arm_action()
            and self._cur_execute_task.is_task_type_fork_action()
        ):
            if self._idle_delay_ct < DELAY_IDLE_FOR_RISK_ACTION_CT:
                self._idle_delay_ct += 1
                return SystemState.BUSY
        else:
            self._idle_delay_ct = 0

        # 切任务过程中 IDLE -> BUSY
        if self._task_to_switch:
            if self._busy_switch_ct < STAY_BUSY_ON_TASK_SWITCH_CT:
                self._busy_switch_ct += 1
                return SystemState.BUSY
            else:
                self._busy_switch_ct = 0
                self._task_to_switch = None
        else:
            self._busy_switch_ct = 0

        return SystemState.IDLE

    def check_send_alarm_on_status(self, state):
        # 货码告警上报，拉大上报间隙
        if self._cnt % 5 == 0 and state in (
            SystemState.SCAN_ERROR,
            SystemState.SHELF_SN_ERROR,
        ):
            if state == SystemState.SCAN_ERROR:
                alarm_code = ALARM_CODE_NO_RECOGNIZE_SHELF_SN
            else:
                alarm_code = ALARM_CODE_SHELF_SN_MISMATCH

            self.send_alarm(
                ALARM_CATEGORY_6,
                alarm_code,
                ALARM_STATUS_PULSE,
                ALARM_GRADE_NORMAL,
            )

    def upload_status(self):
        try:
            cur_pos = self._srp_wrapper.get_cur_pose()
            alarm_major_type, alarm_sub_type = self.get_alarm_type_code()
            battery_info = self._srp_wrapper.get_battery_info()
            if self._cur_execute_task is not None:
                self._cur_task_id = self._cur_execute_task.task_id
                self._cur_sub_task_id = self._cur_execute_task.sub_task_id
            if self._release_state != 0:
                self._cur_execute_task = None
                self._cur_task_id = self._cur_release_task_id
                self._cur_sub_task_id = self._cur_release_sub_task_id
            if self._dm_code_type_ldm != '':
                dmcode_upload = self._dm_code_type_ldm
            elif self._dm_code_type_map != '':
                dmcode_upload = self._dm_code_type_map
            else:
                dmcode_upload = self._dm_code_type_detect

            assert isinstance(dmcode_upload, str)
            if not dmcode_upload.isascii():
                if self._cnt % 10 == 0:
                    _logger.warning(f'dmcode is not ascii-only: {dmcode_upload}')
                dmcode_upload = '__'
            if len(dmcode_upload) > 2:
                dmcode_upload = dmcode_upload[0:2]

            s_state = self.get_device_state()
            s_state = self.get_state_to_override_for_some_case(s_state)

            MiscUtils.append_unique(self._latest_states, s_state)

            self.check_send_alarm_on_status(s_state)

            dat = self._protocol.pack_status_upload_req(
                device_id=self.get_robot_id(),
                msg_sn=self._server_wrapper.get_msg_sn(),
                task_id=self._cur_task_id,
                subtask_id=self._cur_sub_task_id,
                system_state=s_state.value,
                x=cur_pos['x'],
                y=cur_pos['y'],
                angle=cur_pos['angle'],
                dmcode_type=dmcode_upload,
                battery_level=battery_info['percent'],
                battery_temperature=battery_info['temperature'],
                battery_current=battery_info['current'],
                battery_voltage=battery_info['voltage'],
                linear_velocity=self._srp_wrapper.get_linear_velocity(),
                angular_velocity=self._srp_wrapper.get_angle_velocity(),
                main_warning=alarm_major_type,
                sub_waring=alarm_sub_type,
            )
            # 即使出现异常，不要掉线
            try:
                if self._config.is_device_riser_rotate():
                    # 探测货架
                    if (
                        self._cur_execute_task
                        and (
                            (
                                self._cur_execute_task.is_task_type_shelf_sn_detect()
                                and not self._task_thread.is_cur_task_running()
                            )
                            or self._cur_execute_task.is_task_type_raise_shelf_only()
                        )
                        and self._srp_wrapper.is_detect_action_task_finish(
                            self._task_thread._action_no
                        )
                        and self._task_thread._action_no != self._pre_action_no
                    ):
                        shelf_id = self._task_thread.get_detect_shelf_sn()
                        shelf_angle = self._task_thread.get_detect_shelf_angle()
                        if shelf_id != '':
                            self._shelf_id = shelf_id
                        if self._cnt % 10 == 0:
                            _logger.info(f'detected shelf info: {shelf_id}, {shelf_angle:.1f}°')
                        self._protocol.pack_shelf_actuator_detect_ctrl(dat, shelf_id, shelf_angle)
                    else:
                        shelf_id = ''
                        shelf_x = 0
                        shelf_y = 0
                        shelf_angle = 0

                        if self._srp_wrapper.is_load_free():
                            self._check_load_ok = True
                        elif self._srp_wrapper.is_load_full() and not self._check_load_ok:
                            # 进程刚起来如果为满载，扫一下码
                            _logger.info('load full, will do detect action')
                            self._task_thread._do_execute_action(133, 1, 0)
                            self._check_load_ok = True

                            # 扫完码后同步一下保存，后面的 get_shelf_info() 可能拿不到二维码
                            shelf_id = self._task_thread.get_detect_shelf_sn()
                            shelf_angle = self._task_thread.get_detect_shelf_angle()
                            if shelf_id != '':
                                self._shelf_id = shelf_id
                            _logger.info(f'detected shelf info: {shelf_id}, {shelf_angle:.1f}°')

                        if self._srp_wrapper.is_load_full() and self._check_load_ok:
                            shelf_id, _ = self._srp_wrapper.get_shelf_info()
                            if shelf_id == '':
                                shelf_id = self._shelf_id
                            else:
                                self._shelf_id = shelf_id
                            shelf_x = cur_pos['x']
                            shelf_y = cur_pos['y']
                            shelf_angle = self._srp_wrapper.get_shelf_angle_in_global(ANGLE_180)

                            # 去除货架上报误差: 货架角度误差小于阀值时,上传时略去偏差,否则上传真实值
                            upload_shelf_angle = AngleUtils.to_90n(shelf_angle)
                            if not AngleUtils.equal_norm(
                                AngleUtils.normalize_360(shelf_angle),
                                AngleUtils.normalize_360(upload_shelf_angle),
                                UPLOAD_SHELF_ANGLE_FILTER,
                            ):
                                upload_shelf_angle = shelf_angle
                            upload_shelf_angle = AngleUtils.normalize_180(upload_shelf_angle)
                        else:
                            upload_shelf_angle = 0

                        if shelf_id != '' and self._cnt % 10 == 0:
                            _logger.info(
                                'upload shelf info(id, state, angle): '
                                f'{shelf_id}, {self.get_actuator_state()}, '
                                f'{upload_shelf_angle:.1f}/{shelf_angle:.1f}°'
                            )
                        self._protocol.pack_shelf_actuator_status(
                            dat,
                            shelf_id,
                            self.get_actuator_state(),
                            shelf_x=shelf_x,
                            shelf_y=shelf_y,
                            shelf_angle=upload_shelf_angle,
                        )
                elif self._config.is_device_roller():
                    self._check_load_ok = True
                    roller_0, roller_1, roller_2, roller_3 = self.get_roller_state()
                    self._protocol.pack_roller_status(
                        dat, roller0=roller_0, roller1=roller_1, roller2=roller_2, roller3=roller_3
                    )
                elif self._config.is_device_aging() or self._config.is_device_smt():
                    # 老化工装复用smt结构
                    smt_state = self._srp_wrapper.get_smt_state()
                    self._protocol.pack_smt_status(dat, smt_state)
                elif self._config.is_device_all_direction():
                    is_arm_executing = self._srp_wrapper.is_arm_action_executing()
                    arm_load_state = self._srp_wrapper.is_load_full()
                    agv_load_state = self.get_arm_agv_load_arry()
                    self._protocol.pack_arm_status(
                        dat, is_arm_executing, arm_load_state, agv_load_state
                    )
                elif self._config.is_agv_model_gulf():
                    fork_height = int(self._srp_wrapper.get_fork_height() * 1000)
                    load_state = self._srp_wrapper.is_load_full()
                    self._protocol.pack_gulf_status(dat, fork_height, load_state)
                else:
                    self._check_load_ok = True
                    if not self._config.is_device_all_direction() and self._cnt % 10 == 0:
                        _logger.warning('null actuator')
                    self._protocol.pack_none_actuator_status(dat)
            except BaseException as e:
                _logger.error(e, exc_info=True)

            self.send_request(dat)
            self._cnt += 1

            if self._cnt % 10 == 0:
                _logger.info(
                    f'state:{self._cur_task_id}.{self._cur_sub_task_id} {s_state.name} '
                    f'{dmcode_upload} {self._task_thread.get_pose_info()}'
                )
                if not self._task_thread.check_cur_pose_valid():
                    _logger.info('long distance un detect dmcode')

            if self._cnt % 600 == 0:
                self._cnt = 0
                self.monit_charge_state()

            fault_list = self._srp_wrapper.get_fault_codes()
            if fault_list != self.last_fault_list:
                for fault_code in fault_list:
                    self.send_alarm(
                        category=fault_code // 1000,
                        type_code=fault_code % 1000,
                        status=ALARM_STATUS_ON,
                        grade=ALARM_GRADE_HIGH,
                    )
                for fault_code in self.last_fault_list:
                    if fault_code not in fault_list:
                        self.send_alarm(
                            category=fault_code // 1000,
                            type_code=fault_code % 1000,
                            status=ALARM_STATUS_OFF,
                            grade=ALARM_GRADE_HIGH,
                        )
                self.last_fault_list = fault_list

            self.start_upload_status_timer()
        except BaseException as e:
            _logger.error(f'Upload status exception: {e}', exc_info=True)

    def monit_charge_state(self):
        if self._cur_execute_task and self._cur_execute_task.is_charge_task():
            self._task_thread.stop_charge_if_full()
            # vsc存在充一会儿自己断电的问题，尝试重发解决
            self._task_thread.resend_charge_cmd_if_error()

    def get_roller_state(self):
        roller_0 = roller_1 = roller_2 = roller_3 = 0
        load_state = self._srp_wrapper.get_multi_load_state()
        if load_state & 0x1 != 0:
            roller_0 = 1
        if load_state & 0x2 != 0:
            roller_1 = 1
        if load_state & 0x4 != 0:
            roller_3 = 1
        if load_state & 0x8 != 0:
            roller_2 = 1
        return roller_0, roller_1, roller_2, roller_3

    def get_arm_agv_load_arry(self):
        load_arry = []
        load_state = self._srp_wrapper.get_multi_load_state()
        for i in range(0, 10):
            if ((1 << i) & load_state) != 0:
                load_arry.append(1)
            else:
                load_arry.append(0)
        return load_arry

    def upload_battery_status(self):
        battery_info = self._srp_wrapper.get_battery_info()
        _logger.info(f'Upload battery status: {battery_info}')
        dat = self._protocol.pack_upload_battery_status_req(
            self.get_robot_id(), self._server_wrapper.get_msg_sn(), battery_info
        )
        self.send_request(dat)

    def request_register(self):
        _logger.info('client device request register')
        dat = self._protocol.pack_register_request(
            device_id=self.get_robot_id(),
            msg_sn=self._server_wrapper.get_msg_sn(),
            device_type=self._config.get_device_type(),
        )
        self.send_request(dat)

    def request_charge_maintain(self):
        _logger.info('Device request charge maintain')
        dat = self._protocol.pack_charge_full_req(
            device_id=self.get_robot_id(),
            msg_sn=self._server_wrapper.get_msg_sn(),
            type_code=ChargeMaintain.DeviceMaintain,
        )
        self.send_request(dat)

    def response_no_payload_move(self, msg_sn):
        dat = self._protocol.pack_no_payload_move_resp(self.get_robot_id(), msg_sn)
        self.send_response(dat)

    def response_common_cmd(self, msg_sn, type_code, result=RESPONSE_OKAY, err_code=None):
        dat = self._protocol.pack_common_rsp(
            device_id=self.get_robot_id(),
            msg_sn=msg_sn,
            type_code=type_code,
            result=result,
            err_code=err_code,
        )
        self.send_response(dat)

    @check_and_init_server_wrapper_server
    def send_data(self, dat):
        self._server_wrapper.send_data(dat)

    def receive_data(self, recv_dat):
        self.do_recv_dat_from_server(recv_dat)

    def receive_data_from_alarm_server(self, dat):
        ba_header = dat[:ALARM_HEADER_LEN]
        ba_body = dat[ALARM_HEADER_LEN:]
        header = self._protocol.unpack_alarm_header(ba_header)
        result, _ = self._protocol.unpack_alarm_response(ba_body)
        if result != RESPONSE_OKAY:
            _logger.error('response from alarm server is ERROR')
        else:
            _logger.info('response from alarm server is OKAY')

    def process_register_rsp(self, dat):
        _logger.info('receive register response')
        result = self._protocol.unpack_register_rsp(dat)
        if result['result'] == RESPONSE_OKAY:
            self._dm_code_type = result['dm_code']
            _logger.info('register OKay')

            self.reset_lost_conn_timer()
            self.start_upload_battery_status_timer()

    def process_device_ability_req(self, msg_sn):
        _logger.info('get request device ability from server')
        rsp = self._protocol.pack_common_rsp(
            device_id=self.get_robot_id(),
            msg_sn=msg_sn,
            type_code=MSG_RSP_DEVICE_ABILITY,
            result=RESPONSE_OKAY,
        )
        self.send_response(rsp)
        dat = self._protocol.pack_upload_device_ability(self.get_robot_id(), msg_sn)
        self.send_response(dat)

    def process_cfg_upload_status_req(self, msg_sn, dat):
        _logger.info('Receive status config from server:')
        cfg = self._protocol.unpack_cfg_upload_status_req(dat)
        _logger.info(cfg)
        if cfg:
            self._config.set_upload_status_interval(cfg['interval'] / 1000)
        rsp = self._protocol.pack_common_rsp(
            self.get_robot_id(), msg_sn, MSG_RSP_CFG_UPLOAD_STATUS, RESPONSE_OKAY
        )

        # 初始交互完成后开始上传状态
        self.start_upload_status_timer()

        self.send_response(rsp)

    def process_cfg_warning_server_req(self, msg_sn, dat):
        _logger.info('Receive warning server config from server: ')
        cfg = self._protocol.unpack_cfg_warning_server_req(dat)
        _logger.info(cfg)
        if cfg:
            server = (cfg['ipv4'], cfg['port'])
            self._server_wrapper.set_alarm_server(server)
        rsp = self._protocol.pack_common_rsp(
            self.get_robot_id(), msg_sn, MSG_RSP_CFG_WARN_SERVER, RESPONSE_OKAY
        )
        self.send_response(rsp)

    def process_cfg_time_sync_req(self, msg_sn, dat):
        _logger.info('Receive time sync from server: ')
        cfg = self._protocol.unpack_cfg_time_sync_req(dat)
        if cfg:
            _logger.info(f'sync time cfg: {cfg}')
            if cfg['sync_type'] == 0:
                ipv4, ipv6, port = cfg['ipv4'], cfg['ipv6'], cfg['port']
                interval_min = cfg['interval']  # min
                MiscUtils.setup_timesyncd(ipv4 or ipv6, port, interval_min)
            elif cfg['sync_type'] == 1:
                timezone, cur_time = cfg['timezone'], cfg['cur_time']
                MiscUtils.set_current_time(timezone, cur_time)
            else:
                _logger.error(f'unkown sync_type: {cfg["sync_type"]}')
        rsp = self._protocol.pack_common_rsp(
            self.get_robot_id(), msg_sn, MSG_RSP_CFG_TIME_SYNC, RESPONSE_OKAY
        )
        self.send_response(rsp)

    def process_cfg_global_precision(self, msg_sn, dat):
        _logger.info('Receive global precision config from server: ')
        cfg = self._protocol.unpack_cfg_global_precision(dat)
        _logger.info(cfg)
        if cfg:
            self._config.set_global_precision(cfg)
        rsp = self._protocol.pack_common_rsp(
            self.get_robot_id(), msg_sn, MSG_RSP_CFG_GLOBAL_PRECISION, RESPONSE_OKAY
        )
        self.send_response(rsp)

    def process_cfg_timeout(self, msg_sn, dat):
        _logger.info('Receive time out config from server: ')
        live_time, timeout = self._protocol.unpack_cfg_timeout(dat)
        if live_time:
            self._config.set_msg_live_time(live_time / 1000)
            self._config.set_msg_resend_interval(timeout / 1000)
        rsp = self._protocol.pack_common_rsp(
            self.get_robot_id(), msg_sn, MSG_RSP_CFG_TIMEOUT, RESPONSE_OKAY
        )
        self.send_response(rsp)

    def process_cfg_upload_battery(self, msg_sn, dat):
        _logger.info('Receive upload battery config from server: ')
        cfg = self._protocol.unpack_cfg_upload_battery(dat)
        _logger.info(cfg)
        if cfg:
            self._config.set_upload_battery_status_interval(cfg['interval'])
        rsp = self._protocol.pack_common_rsp(
            self.get_robot_id(), msg_sn, MSG_RSP_CFG_UPLOAD_BATTERY, RESPONSE_OKAY
        )
        self.send_response(rsp)

        # 停止定时器
        self.start_upload_battery_status_timer()

    def process_change_map(self, msg_sn, dat):
        _logger.info('Receive change map request from server')
        self.response_common_cmd(msg_sn, MSG_RSP_CHANGE_MAP)
        dat = self._protocol.unpack_changed_map_req(dat)
        _logger.info(dat)
        self._dm_code_type_ldm = dat['dmcode_type']
        self._task_thread.changed_map(dat)

    def process_changed_switch(self, msg_sn, dat):
        _logger.info('Receive changed switch >>>> request from server: ')
        self.response_common_cmd(msg_sn, MSG_RSP_SWITCH_NAV_MODE)
        dat = self._protocol.unpack_changed_switch_req(dat)
        _logger.info(dat)
        if 'dmcode_type' in dat:
            self._dm_code_type_ldm = dat['dmcode_type']
        else:
            self._dm_code_type_ldm = ''
        if self._task_thread._is_processing:
            return
        self._task_thread.changed_switch(dat)

    def upload_system_versions(self):
        sros_info = self._srp_wrapper.get_info()
        if sros_info is None:
            _logger.error('process_upload_versions(): Sros info is None')
            return
        versions = {
            'system_version': sros_info.sros_version_str,
            'hardware_version': sros_info.hardware_version,
            'src_version': sros_info.src_version_str,
            'serial_no': sros_info.vehicle_serial_no,
            'vendor': DEVICE_VENDOR_ID,
            'device_type': self._config.get_device_type(),
        }
        dat = self._protocol.pack_version_upload_req(
            self.get_robot_id(), self._server_wrapper.get_msg_sn(), versions
        )
        self.send_request(dat)

    def process_command_task(self, type_code, dat):
        # 消息类型和任务类型的枚举是一致的，这边不做转换
        task = self._protocol.unpack_command_req(dat, type_code)
        if self._cur_execute_task is None or (
            self._cur_execute_task.task_id != task.task_id
            or self._cur_execute_task.sub_task_id != task.sub_task_id
        ):
            if (
                type_code == MSG_REQ_PAUSE
                and self._cur_execute_task
                and self._cur_execute_task.task_type != type_code
            ):
                self._cur_pause_task = self._cur_execute_task
            elif type_code == MSG_REQ_CONTINUE:
                # 如果有记录暂停前任务，或者当前任务为暂停
                if self._cur_pause_task or (
                    self._cur_execute_task and self._cur_execute_task.task_type == MSG_REQ_PAUSE
                ):
                    self._cur_execute_task = self._cur_pause_task
                    self._cur_pause_task = None

                # 针对部分异常，给个通过继续重试的恢复机会
                device_state = self.get_device_state()
                if device_state in (SystemState.ROLL_FAILED,):
                    self._srp_wrapper.cancel_task()
                    self._task_thread.cancel_task()

                return
            elif type_code in (MSG_REQ_STOP_MOVE, MSG_REQ_CANCEL):
                self._cur_pause_task = None
            self._cur_execute_task = task

    # TODO: zz: 下面两个函数，会在载货检查后执行 顶/放 货架动作，调用的比较早，可能在小车处于急停
    #   或其他异常状态时，收到任务就直接执行，如果 sros 那边没拦截可能有安全隐患

    def check_and_raise_shelf_for_payload_move(self, dat, task_type):
        # NOTE: 执行的动作任务都在独立线程的协程循环中排队，当前状态不代表轮到动作执行时的
        # 系统状态，所以动作真正执行前还会需要再次同步系统状态来检查执行条件
        if not self._srp_wrapper.is_load_full():
            this_task = self._protocol.unpack_move_req(dat, task_type)
            if this_task.is_no_detect_raise():
                self._task_thread.do_async_action(4, 11, 100)
            else:
                self._task_thread.do_async_action(4, 1, 0)
            _logger.warning('agv load free, queue the action to raise shelf')
            return False
        return True

    def check_and_put_shelf_for_no_payload_move(self):
        if self._srp_wrapper.is_load_full():
            device_type = self._config.get_device_type()
            _logger.warning(f'load full on no payload move! device_type: {device_type}')

            # 内部会判断是否应该执行放货架动作
            self._task_thread._do_put_shelf()

            # 滚筒车移动时不考虑载货状态，取货后移动发的可能还是空车移动；其他车要求载货状态匹配
            return device_type == DeviceType.ROLLER
        return True

    def process_move_req(self, msg_sn, type_code, dat):
        task_type = TaskType.Unknown
        if type_code == MSG_REQ_NO_PAYLOAD_LINEAR_MOVE:
            _logger.info('receive linear no payload move task from server: ')
            if not self.check_and_put_shelf_for_no_payload_move():
                return
            task_type = TaskType.No_Payload_Linear_Move
            self.response_no_payload_move(msg_sn)
        elif type_code == MSG_REQ_CHARGE:
            _logger.info('receive charge task from server: ')
            task_type = TaskType.Charge_Task
            self.response_common_cmd(msg_sn, MSG_RSP_CHARGE)
        elif type_code == MSG_REQ_SLAM_NAV:
            _logger.info('Receive Slam Nav task from server: ')
            task_type = TaskType.Slam_Nav
            self.response_common_cmd(msg_sn, MSG_RSP_SLAM_NAV)
        elif type_code == MSG_REQ_RAISE_SHELF:
            _logger.info('Receive execute Raise Shelf task from server: ')
            task_type = TaskType.Raise_Shelf_Action
            self.response_common_cmd(msg_sn, MSG_RSP_RAISE_SHELF)
        elif type_code == MSG_REQ_PUT_SHELF:
            _logger.info('Receive execute Put Shelf from server: ')
            task_type = TaskType.Put_Shelf_Action
            self.response_common_cmd(msg_sn, MSG_RSP_PUT_SHELF)
        elif type_code == MSG_REQ_LINEAR_MOVE_AFTER_RAISE_SHELF:
            _logger.info('Receive execute Linear Move After Raise Shelf from server: ')
            task_type = TaskType.Linear_Move_After_Raise_Shelf
            if not self.check_and_raise_shelf_for_payload_move(dat, task_type):
                return
            self.response_common_cmd(msg_sn, MSG_RSP_LINEAR_MOVE_AFTER_RAISE_SHELF)
        elif type_code == MSG_REQ_LINEAR_MOVE_AFTER_PUT_SHELF:
            _logger.info('Receive execute Linear Move After Put Shelf from server: ')
            task_type = TaskType.Linear_Move_After_Put_Shelf
            self.response_common_cmd(msg_sn, MSG_RSP_LINEAR_MOVE_AFTER_PUT_SHELF)
        elif type_code == MSG_REQ_NO_PAYLOAD_ARC_MOVE:
            _logger.info('Receive execute Arc no playload move from server: ')
            task_type = TaskType.No_Payload_Arc_Move
            self.response_common_cmd(msg_sn, MSG_RSP_NO_PAYLOAD_ARC_MOVE)
        elif type_code == MSG_REQ_ARC_MOVE_AFTER_RAISE_SHELF:
            _logger.info('Receive execute Arc Move After Raise Shelf from server: ')
            task_type = TaskType.Arc_Move_After_Raise_Shelf
            if not self.check_and_raise_shelf_for_payload_move(dat, task_type):
                return
            self.response_common_cmd(msg_sn, MSG_RSP_ARC_MOVE_AFTER_RAISE_SHELF)
        elif type_code == MSG_REQ_ARC_MOVE_AFTER_PUT_SHELF:
            _logger.info('Receive execute Arc Move After Put Shelf from server: ')
            task_type = TaskType.Arc_Move_After_Put_Shelf
            self.response_common_cmd(msg_sn, MSG_RSP_ARC_MOVE_AFTER_PUT_SHELF)
        elif type_code == MSG_REQ_ROLLER_CTRL:
            _logger.info('Receive execute roller control from server: ')
            task_type = TaskType.Roller_Control
            self.response_common_cmd(msg_sn, MSG_RSP_ROLLER_CTRL)
        elif type_code == MSG_REQ_DETECT_CTRL:
            _logger.info('Receive shelf detect control from server: ')
            task_type = TaskType.Shelf_SN_Detect
            self.response_common_cmd(msg_sn, MSG_RSP_DETECT_CTRL)
        elif type_code == MSG_REQ_LINEAR_NO_PAYLOAD_MULTI_PATH_MOVE:
            _logger.info('no pyload multi path move task')
            task_type = TaskType.Multi_Path_No_Payload_Move
            if (
                self._config.is_agv_model_gulf()
                and abs(self._srp_wrapper.get_fork_height() - 0.3) > 0.2
            ):
                this_task = self._protocol.unpack_move_req(dat, task_type)
                if not this_task.is_task_type_fork_action():
                    self.reset_task_state()
                    self._task_thread.do_async_action(
                        10161, 0, this_task.actuator_info.actuator_raise_height
                    )
                    _logger.info('error command: wait for lift fork')
                    return
            self.response_common_cmd(msg_sn, MSG_RSP_LINEAR_NO_PAYLOAD_MULTI_PATH_MOVE)
        elif type_code == MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF:
            _logger.info('linear multi path move task after rasie self')
            task_type = TaskType.Multi_Path_Move_After_Raise_Shelf
            if not self.check_and_raise_shelf_for_payload_move(dat, task_type):
                return
            self.response_common_cmd(msg_sn, MSG_RSP_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF)
        elif type_code == MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_PUT_SHELF:
            _logger.info('linear multi path move task after put self')
            task_type = TaskType.Multi_Path_Move_After_Put_Shelf
            self.response_common_cmd(msg_sn, MSG_RSP_LINEAR_MULTI_PATH_MOVE_AFTER_PUT_SHELF)
        elif type_code == MSG_REQ_ARM_FORK_LOAD_ACTION:
            _logger.info('multi move with arm load action')
            task_type = TaskType.Arm_Fork_Load_Action
            self.response_common_cmd(msg_sn, MSG_RSP_ARM_LOAD_ACTION)
        elif type_code == MSG_REQ_ARM_FORK_UNLOAD_ACTION:
            _logger.info('multi move with arm unload action')
            task_type = TaskType.Arm_Fork_Unload_Action
            self.response_common_cmd(msg_sn, MSG_RSP_ARM_UNLOAD_ACTION)
        elif type_code in (
            TaskType.Smt_Multi_Path_Move,
            TaskType.Smt_Load_Action,
            TaskType.Smt_Unload_Action,
        ):
            task_type = TaskType(type_code)
            _logger.info(f'Req: {type_code:#x}({task_type.name})')
            self.response_common_cmd(msg_sn, task_type + 1)

        cur_task = self._protocol.unpack_move_req(dat, task_type)
        if cur_task is None:
            return

        # # 解抱闸恢复过程中，不接受任务
        # if self._brake_delay_timer:
        #     _logger.warning("wait brake switch state OFF")
        #     return

        if cur_task.is_start_charge():
            _logger.info('Start charge')

        if cur_task.is_stop_charge():
            _logger.info('Stop charge')

        if cur_task.is_move_backward():
            _logger.info('Move backward: ' + str(cur_task.move_type))

        if cur_task.is_move_still() and task_type not in (
            # 顶升/下降 货架，不受 move_type=9 限制
            TaskType.Put_Shelf_Action,
            TaskType.Raise_Shelf_Action,
            # 放货架叠加移动，放货架那一步不受 move_type=9 限制，限制移动在后面处理
            TaskType.Linear_Move_After_Put_Shelf,
            TaskType.Multi_Path_Move_After_Put_Shelf,
            TaskType.Arc_Move_After_Put_Shelf,
        ):
            _logger.info('Move still, not exectue')
            return

        # smt 车载货状态与移动类型校验
        if not self._task_thread.check_smt_move_against_load_state(cur_task):
            return

        # smt/老化工装 车移动中同时调高调宽
        if cur_task.is_execute_action_when_move:
            _logger.info('smt adjust height on move')
            self._task_thread._do_smt_adjust_height_and_width(cur_task, is_async=True)
            self._task_thread._do_aging_adjust_height_and_width(cur_task, is_async=True)

            # 异步调宽调高时同步工装状态到当前任务，避免任务移动结束后调整使用的是旧的工装状态
            thread_task = self._task_thread._cur_execute_task
            if thread_task and thread_task.actuator_info:
                thread_task.actuator_info = cur_task.actuator_info

        # 由于会不断接收到重复移动指令，根据坐标和角度过滤
        if self._cur_execute_task and self._cur_execute_task.is_duplicated_task(cur_task):
            if (
                self.is_system_state_idle()
                and cur_task.is_task_execute_repeatable()
                and not self._srp_wrapper.is_executing_action()
            ):
                self._ignore_count += 1
                if self._ignore_count < 5:
                    _logger.info(f'ignore same target move request {self._ignore_count}')
                    return
                elif self._cur_execute_task.is_task_type_arm_action():
                    _logger.info('can not restart arm or fork action')
                    return
                else:
                    _logger.info('will do the same task again, even it is succeed before')
            else:
                self._ignore_count = 0
                _logger.info(f'ignore same target move request {self._ignore_count}')
                return
        self._ignore_count = 0

        self._pre_action_no = self._srp_wrapper.get_action_no()
        if self._task_thread.has_rotate_path():
            _logger.warning('wait rotate path finish before start new task')
            return

        # 由于自动上报的状态存在时间差，因此在处理任务前主动请求查询系统状态
        self._srp_wrapper.fetch_hardware_state()
        self._srp_wrapper.fetch_system_state()

        if self._srp_wrapper.is_fault_error():
            _logger.error('Hardware has fault errors, ignore task')
            return

        # 当前动作任务未结束时，忽略接收到的任务，解决正在执行动作任务时又接收到下一个同一个动作任务
        # 解决移动结束时增加了旋转调整的旋转路径，导致执行失败触发路径替换小车一直旋转停不下来的问题
        if self._task_thread.is_waiting_cur_task_finish():
            _logger.warning('Ignore task when current task is not finish')
            return

        # 当前是充电任务时，如果之前是充电任务或停止充电任务，直接返回防止调整旋转导致碰坏充电桩
        if (
            self._cur_execute_task
            and cur_task.is_start_charge()
            and self._cur_execute_task.is_charge_task()
        ):
            _logger.info('ignore current charge task as last task is start or stop charge task')
            return

        if self._srp_wrapper.is_emergency_state():
            _logger.info('Ignore task in emergency state')
            return

        if self._srp_wrapper.is_brake_sw_on():
            _logger.info('Ignore task in brake state')
            return

        if not self._srp_wrapper.is_location_okay():
            _logger.info('Ignore task when location not OKAY')
            return

        _logger.info(cur_task.__str__())

        # 上一个任务是圆弧路径时，如果接收到的下一个任务目标点在介于圆弧起点和终点之间，则忽略该任务
        if self._cur_execute_task and self._cur_execute_task.is_task_arc_move():
            target_pose = cur_task.get_move_target()
            if self._cur_execute_task.is_between_arc_points(target_pose['x'], target_pose['y']):
                _logger.error('current task target is between arc points, ignore task')
                return

        # 正在充电时，忽略所有任务(停止充电任务除外)
        if self._srp_wrapper.is_charging() and not cur_task.is_stop_charge():
            _logger.warning('ignore task when in charging state')
            return

        cur_pose = self._srp_wrapper.get_cur_pose()

        # 如果接收到放下货架任务，但是当前没有背货架
        if cur_task.is_task_put_shelf() and not self._srp_wrapper.is_load_full():
            _logger.warning('receive put shelf task but is LOAD_FREE')

        # 顶升货架时，如果发现货架已经举升
        if cur_task.is_task_type_raise_shelf_only() and self._srp_wrapper.is_load_full():
            _logger.warning('shelf has been raised when receive raise shelf task')

        # 仅举升货架，执行动作前判断当前位置和调度系统发送的位置是否在可接收误差范围内
        if (
            (cur_task.is_task_type_raise_shelf_only() and not cur_task.is_auto_identify_shelf_leg())
            or cur_task.is_task_type_roller()
            or cur_task.is_task_type_put_shelf_only()
        ):
            is_ignore_angle = cur_task.is_task_type_raise_shelf_only()
            if not cur_task.is_at_target_pos(cur_pose, is_ignore_angle):
                _logger.error(
                    'Current robot pos is not where action task should be executed, ignore action'
                )
                return

        # 非空闲状态只允许任务id相同的任务透传，以便支持连续移动
        task_id, sub_task_id = cur_task.get_task_id()
        self._cur_task_id, self._cur_sub_task_id = task_id, sub_task_id
        if not self.is_system_state_idle():
            if self._cur_execute_task:
                if not self._cur_execute_task.is_same_task_id(task_id, sub_task_id):
                    _logger.info('system is not in idle state and task id changed')

                    # 移动中，ldm 切移动任务，直接取消旧任务
                    if (
                        self._cur_execute_task.is_task_movement_mini()
                        and cur_task.is_task_movement_mini()
                    ):
                        _logger.warning(
                            f'cancel move for task switch: {cur_task.get_task_id_str()}'
                        )
                        self._srp_wrapper.cancel_task()
                        self.reset_task_state()
                        self._task_to_switch = cur_task
                        return

                    _logger.info(f'ignore task: {cur_task.get_task_id_str()}')
                    return

                else:
                    _logger.info(
                        'sys state not idle but task id is same, '
                        f'state: {self._srp_wrapper.get_sys_state()}'
                    )
                    # 当前的曲线类型替换成了直线类型，且目标角度变动很大，可能是重新规划了路径，
                    # 取消当前任务，等新任务
                    cur_target_angle = self._cur_execute_task.get_target_angle() / 1000
                    new_target_angle = cur_task.get_target_angle() / 1000
                    if (
                        not AngleUtils.equal_norm(
                            cur_target_angle, new_target_angle, threshold=ANGLE_30
                        )
                        and cur_task.is_task_linear_move()
                        and (
                            self._cur_execute_task.is_task_arc_move()
                            or self._cur_execute_task.is_task_type_with_multi_path_move()
                        )
                    ):
                        _logger.info(
                            '从曲线类型替换成了直线类型，且目标点角度有很大变化：'
                            f'{cur_target_angle:.3f}->{new_target_angle:.3f} deg'
                        )
                        self._srp_wrapper.cancel_task()
                        self.reset_task_state()
                        return

                    # 调度系统会发很多很短的路径，累积到一定距离后再处理
                    if self.is_ignore_path(cur_task):
                        if (
                            cur_task.is_task_linear_move()
                            and self._task_thread.may_replace_last_line(
                                cur_task.move_target.x, cur_task.move_target.y
                            )
                        ) or (
                            cur_task.is_task_type_no_payload_linear_move()
                            and cur_task.is_auto_identify_shelf_leg()
                            and self._cur_execute_task.task_detail == TaskItem.Normal
                        ):
                            _logger.info('is path replace')
                        else:
                            _logger.info('ignore short path from server')
                            return

                    # 如果移动方向类型不匹配，如前进时收到后退，或回退时收到前进，应马上取消当前路径
                    # 立即执行新路径，否则可能会导致往前走了很长距离，然后再后退
                    if self._cur_execute_task.is_move_backward() != cur_task.is_move_backward():
                        _logger.info('move direction change, cancel current task')
                        self._srp_wrapper.cancel_task()
                        self.reset_task_state()
                        return
            else:
                _logger.warning('system state not idle but no task executing, who start the task?')
                return

        # 路径队列中还有路径未发送，等路径队列都发送完上一个任务后才允许继续发送路径
        if self._task_thread.has_pending_path():
            _logger.warning('Path in last task wait to send, ignore current receive task')
            return

        # 任务还在处理重时，可能是异步的(async/await)，避免导致多条任务同时进入执行状态
        if self._task_thread.is_task_processing():
            _logger.info('Task is processing, wait')
            return

        if self._srp_wrapper.is_raising_shelf() or self._srp_wrapper.is_putting_shelf():
            _logger.info('a task start by other client ')
            return
        self._cur_execute_task = cur_task
        if cur_task.is_no_detect_raise() and cur_task.get_shelf_sn_from_task() != '':
            _logger.info('no detect raise shelf')
            self._shelf_id = cur_task.get_shelf_sn_from_task()

        self._task_thread.start(cur_task)

    # 是否忽略系统下发的短路径，等路径累计到超过长度再处理
    def is_ignore_path(self, task):
        if self._cur_execute_task is None:
            return False

        # 由于系统发的路段包含很多10cm左右的路段，会导致小车导航速度很慢，因此这里当路径长度达到一定距离后再算路径
        next_target = task.get_move_target()
        cur_target = self._cur_execute_task.get_move_target()
        # # 角度不同时，等待当前任务结束再执行下一个任务
        # if next_target["angle"] != cur_target["angle"]:
        #     return True
        cur_pose = self._srp_wrapper.get_cur_pose()
        if cur_pose is None:
            return False
        remain_distance_mm = self._srp_wrapper.get_move_remain_distance()
        _logger.info(f'remain distance: {remain_distance_mm / 1000:.3f}m')
        if (
            remain_distance_mm < REMAIN_DISTANCE_THRESHOLD
            and not self._task_thread.has_pending_path()
        ):
            _logger.info('task is almost finish, can send short path')
            return True

        # todo 此处可能出问题，简单的通过计算两点之间的距离来估计路径长度，更科学的方法是规划出路径后在判断
        distance = GeometryUtils.calculate_distance(
            cur_pose['x'], cur_pose['y'], next_target['x'], next_target['y']
        )
        _logger.info(f'当前位置距离目标位置{distance / 1000:.3f}m')
        if distance < MIN_PATH_LENGTH:
            _logger.info(
                f'current pos to next target distance short, min req {MIN_PATH_LENGTH / 1000:.3f}m'
            )
            return True

        # 解决当前目标点和下一个目标点距离太近，导致上一条任已发送但是系统状态未变导致继续发送路径报错
        distance = GeometryUtils.calculate_distance(
            cur_target['x'], cur_target['y'], next_target['x'], next_target['y']
        )
        if distance < 200 and task.get_limit_v() == self._cur_execute_task.get_limit_v():
            _logger.info('current target to next target distance short')
            return True
        return False

    # 获取执行机构状态
    def get_actuator_state(self):
        try:
            action_state = self._srp_wrapper.get_action_task_state()
            action_result, err_code = self._srp_wrapper.get_action_task_result()
            if action_state == main_pb2.ActionTask.TaskState.AT_FINISHED:
                if action_result in (main_pb2.TASK_RESULT_OK, main_pb2.TASK_RESULT_NA):
                    if self._srp_wrapper.is_load_full():
                        return ShelfTaskState.Raise_Top
                    elif self._srp_wrapper.is_rotate_put_shelf_action():
                        return ShelfTaskState.Put_Bottom
                    else:
                        return ShelfTaskState.Unknown
                elif action_result == main_pb2.TASK_RESULT_FAILED:
                    if (
                        self._srp_wrapper.is_rotate_put_shelf_action()
                        or self._srp_wrapper.is_rotate_raise_shelf_action()
                    ):
                        return ShelfTaskState.Error
                else:
                    return ShelfTaskState.Unknown
            elif (
                action_state
                in (
                    main_pb2.ActionTask.TaskState.AT_WAIT_FOR_START,
                    main_pb2.ActionTask.TaskState.AT_RUNNING,
                    main_pb2.ActionTask.TaskState.AT_TASK_WAIT_FOR_ACK,
                )
                and not self._srp_wrapper.is_load_full()
            ):
                return ShelfTaskState.Processing
            elif action_state == main_pb2.ActionTask.TaskState.AT_PAUSED:
                return ShelfTaskState.Pause
            else:
                return ShelfTaskState.Unknown
        except BaseException as e:
            _logger.error(f'get actuator state error: {e}', exc_info=True)
        return ShelfTaskState.Unknown

    # 机器人系统状态与上传的设备状态进行协议适配
    def get_device_state(self):
        try:
            # 急停后自动释放
            if self._release_state == 2 and self._srp_wrapper.is_emergency_state():
                _logger.info('auto release because of emergency')
                self._release_state = 0
                # 重置 release task id, 以便紧急状态恢复后，可以重新执行该释放任务
                self._cur_release_task_id = 0
                self._cur_release_sub_task_id = -1
                self.reset_release_timers()
                self._srp_wrapper.cancel_task()

            system_status = self._srp_wrapper.get_sys_state()
            operation_state = self._srp_wrapper.get_operation_state()
            action_state = self._srp_wrapper.get_action_task_state()
            action_result, err_code = self._srp_wrapper.get_action_task_result()

            if self._release_state != 0:
                if self._release_state == 1 and self._srp_wrapper.is_executing_action():
                    _logger.info('catch release state change')
                    self._release_state = 2
                elif self._release_state == 2 and not self._srp_wrapper.is_executing_action():
                    _logger.info('release ok')
                    self._release_state = 0
                _logger.info('wait release')
                return SystemState.WAIT_RELEASE

            # 上报状态需要考虑优先级，如果出现异常，先报异常
            if (
                system_status
                in (
                    main_pb2.SystemState.SYS_STATE_ERROR,
                    main_pb2.SystemState.SYS_STATE_TASK_NAV_NO_WAY,
                    main_pb2.SystemState.SYS_STATE_HARDWARE_ERROR,
                )
                or self._srp_wrapper.is_emergency_state()
                or self._srp_wrapper.is_brake_sw_on()
                or (not self._check_load_ok and self._config.is_device_riser_rotate())
            ):
                return SystemState.ERROR

            if operation_state == main_pb2.SystemState.OPERATION_MANUAL:
                return SystemState.MANUAL_CONTROL

            if not self._task_thread.is_task_processing():
                thread_task = self._task_thread._cur_execute_task

                # 任务处理中发现任务状态异常，上报对应系统异常状态
                task_state_to_sys_state_map = {
                    TaskState.NAV_OFF_PATH: SystemState.NAV_OFF_PATH,
                    TaskState.TASK_WRONG_ANGLE: SystemState.TASK_WRONG_ANGLE,
                    TaskState.SHELF_ANGLE_ERROR: SystemState.SHELF_ANGLE_ERROR,
                    TaskState.SHELF_OFFSET_ERROR: SystemState.SHELF_OFFSET_ERROR,
                    TaskState.LOCK_SPACE_FAILED_TEMP: SystemState.LOCK_SPACE_FAILED_TEMP,
                    TaskState.LOCK_SPACE_FAILED_PERMANENT: SystemState.LOCK_SPACE_FAILED_PERMANENT,
                }

                if thread_task and thread_task.state in task_state_to_sys_state_map:
                    return task_state_to_sys_state_map[thread_task.state]

                raw_sros_task_result_code = self._task_thread.get_raw_sros_task_result_code()
                if self._task_thread.is_execute_raise_shelf_task():
                    # 暂停取消任务会导致 _cur_execute_task 不同步，使用任务线程的 task 来检测二维码
                    assert thread_task is not None
                    # 举升货架时，校验货架id是否匹配，如果从硬件状态获取会有延迟导致上传错误状态
                    shelf_sn = self._task_thread.get_detect_shelf_sn()
                    shelf_sn_from_server = thread_task.get_shelf_sn_from_task()
                    if not thread_task.is_shelf_sn_match(shelf_sn):
                        _logger.error(
                            f'Shelf SN no match: server: {shelf_sn_from_server}, scan: {shelf_sn}'
                        )
                        if shelf_sn == '':
                            return SystemState.SCAN_ERROR
                        else:  # 货架被替换
                            return SystemState.SHELF_SN_ERROR
                elif self._task_thread.is_execute_detect_shelf_task_failed():
                    # 未探测到二维码时，根据任务的探测类型返回异常
                    detect_type = self._task_thread._cur_execute_task.detect_type
                    if detect_type != DetectType.Default:
                        return SystemState.SCAN_ERROR
                    return SystemState.IDLE
                elif self._task_thread.is_execute_roller_task_failed():
                    return ActionErrorCode_To_SyetemState.get(
                        raw_sros_task_result_code, SystemState.ROLL_FAILED
                    )
                elif self._task_thread.is_execute_arm_task_failed():
                    if self._task_thread._retry_arm_task:
                        return SystemState.BUSY
                    else:
                        return SystemState.ERROR

            # 在执行动作任务时，小车系统状态竟然是空闲的
            if self._srp_wrapper.is_executing_action() and self._cur_execute_task:
                if self._cur_execute_task.is_charge_task():
                    return SystemState.BUSY
                elif self._cur_execute_task.is_task_type_shelf() and (
                    self._srp_wrapper.is_raising_shelf() or self._srp_wrapper.is_putting_shelf()
                ):
                    return SystemState.EXECUTE_ACTION
                elif (
                    self._cur_execute_task.is_task_type_roller()
                    and self._srp_wrapper.is_rolling_action()
                ):
                    return SystemState.ROLL_RUNNING
                elif self._cur_execute_task.is_task_type_fork_action():
                    _logger.info('in auto adjust')
                    return SystemState.AUTO_ADJUST
                elif self._cur_execute_task.is_task_type_smt_action():
                    return SystemState.EXECUTE_ACTION
                else:
                    if action_state == main_pb2.ActionTask.TaskState.AT_PAUSED:
                        return SystemState.PAUSE
                    return SystemState.BUSY

            # 只要发了充电命令就是不能返回空闲状态，如果一直充不上电或者充一段时间自动断开需要从下面解决
            if self._cur_execute_task and self._cur_execute_task.is_charge_task():
                if self._srp_wrapper.is_charging():
                    return SystemState.CHARGING
                elif self._task_thread.resend_charge_cmd_time > 4:
                    _logger.info('have not charge ok almost 3min')
                    return SystemState.IDLE
                elif self._task_thread.send_charge_cmd_before_send_stop:
                    _logger.info('have sended charge cmd wait for chargeing')
                    return SystemState.BUSY

            if self._srp_wrapper.is_location_error():
                return SystemState.LOCATE_FAILED

            if self._cur_execute_task and action_state == main_pb2.ActionTask.TaskState.AT_FINISHED:
                if action_result == main_pb2.TASK_RESULT_NA:
                    pass
                elif action_result == main_pb2.TASK_RESULT_OK:
                    if (
                        self._cur_execute_task.is_task_type_fork_load_action()
                        or self._cur_execute_task.is_task_type_fork_unload_action()
                    ):
                        _logger.info('load unload ok')
                        return SystemState.LOAD_UNLOAD_OK
                # 上次任务失败时，会导致上报上次失败的任务(与本次任务并无关系)
                # 故只有系统空闲状态才上报动作错误
                elif (
                    self._srp_wrapper.is_system_idle()
                    and action_result == main_pb2.TASK_RESULT_FAILED
                ):
                    if self._cur_execute_task.is_start_charge():
                        # return SystemState.CHARGE_NO_CONN
                        # return SystemState.CHARGE_FULL
                        _logger.info('charge task not execute by action now')
                    elif (
                        self._srp_wrapper.is_raising_shelf() or self._srp_wrapper.is_putting_shelf()
                    ):
                        return SystemState.RAISE_PUT_ERROR

            if system_status == main_pb2.SystemState.SYS_STATE_TASK_MANUAL_PAUSED or (
                self._cur_execute_task and self._cur_execute_task.task_type == MSG_REQ_PAUSE
            ):
                return SystemState.PAUSE
            elif system_status in (
                main_pb2.SystemState.SYS_STATE_TASK_NAV_WAITING_FINISH_SLOW,
                main_pb2.SystemState.SYS_STATE_TASK_PATH_WAITING_FINISH_SLOW,
            ):
                if self._srp_wrapper.is_move_at_arc():
                    return SystemState.ARC_MOVE
                else:
                    return SystemState.BUSY
            elif system_status in (
                main_pb2.SystemState.SYS_STATE_TASK_PATH_PAUSED,
                main_pb2.SystemState.SYS_STATE_TASK_NAV_PAUSED,
            ):
                return SystemState.OBA_AHEAD
            elif system_status in (
                main_pb2.SystemState.SYS_STATE_TASK_NAV_PATH_ERROR,
                main_pb2.SystemState.SYS_STATE_TASK_MANUAL_PATH_ERROR,
            ):
                return SystemState.NAV_OFF_PATH
            elif system_status == main_pb2.SystemState.SYS_STATE_IDLE:
                if self._task_thread.is_cur_task_running():
                    return SystemState.BUSY
                return SystemState.IDLE
            elif self._srp_wrapper.is_move_at_arc():
                return SystemState.ARC_MOVE
            else:
                return SystemState.BUSY
        except BaseException as e:
            _logger.error(f'Get device state error: {e}', exc_info=True)
            return SystemState.ERROR

    def get_alarm_type_code(self):
        major_type = sub_type = 0
        device_state = self.get_device_state()
        if self._srp_wrapper.is_emergency_state() or self._srp_wrapper.is_brake_sw_on():
            if self._srp_wrapper.is_emergency_cause_by_hit():  # 碰撞
                major_type = ALARM_CATEGORY_6
                sub_type = ALARM_CODE_HIT
            else:  # 急停
                major_type = ALARM_CATEGORY_7
                sub_type = ALARM_CODE_EMERGENCY
        elif device_state == SystemState.SCAN_ERROR:  # 货码不识别
            major_type = ALARM_CATEGORY_6
            sub_type = ALARM_CODE_NO_RECOGNIZE_SHELF_SN
        elif device_state == SystemState.SHELF_SN_ERROR:  # 货码不匹配
            major_type = ALARM_CATEGORY_6
            sub_type = ALARM_CODE_SHELF_SN_MISMATCH
        elif device_state == SystemState.CHARGE_NO_CONN:  # 充电未连接
            major_type = ALARM_CATEGORY_3
            sub_type = ALARM_CODE_FAIL_CONNECT_CHARGE_PILE
        elif device_state == SystemState.OBA_AHEAD:  # 检测到障碍
            major_type = ALARM_CATEGORY_7
            sub_type = ALARM_CODE_DETECT_OBA
        elif self._task_thread.get_lock_space_error_code() >= 3:
            major_type = ALARM_CATEGORY_1
            sub_type = ALARM_CODE_REQ_ROTATE_FAILED_FOREVER
        return major_type, sub_type

    def reset_lost_conn_timer(self):
        if not self._is_running:
            return
        if self._lost_conn_timer is not None:
            self._lost_conn_timer.cancel()
            self._lost_conn_timer = None
        self._lost_conn_timer = Timer(LOST_CONN_TIME_THRESHOLD, self.heart_beat_timeout)
        self._lost_conn_timer.start()

    def start_upload_status_timer(self):
        if self._upload_status_timer:
            self._upload_status_timer.cancel()
            self._upload_status_timer = None
        self._upload_status_timer = Timer(
            self._config.get_upload_status_interval(), self.upload_status
        )
        self._upload_status_timer.start()

    def heart_beat_timeout(self):
        _logger.warning('heart beat timeout')
        if self._server_wrapper._server is not None:
            target = self._server_wrapper._server[0]
            p = MiscUtils.run_cmd(f'ping -q -c 1 -W 3 {target}', wait=True)
            if p.returncode != 0:
                _logger.info(f'ping {target} timeout')
            else:
                _logger.info(f'ping {target} ok')
        self._reconnecting = True
        self.send_alarm(
            ALARM_CATEGORY_1, ALARM_CODE_LOST_CONNECT, ALARM_STATUS_ON, ALARM_GRADE_ERROR
        )

        # 掉线后需要重新注册交互，停止上报信息
        if self._upload_status_timer and self._upload_status_timer.is_alive():
            self._upload_status_timer.cancel()

        self.request_register()
        self.reset_lost_conn_timer()
        self.stop_upload_battery_status_timer()

    def start_upload_battery_status_timer(self):
        self.stop_upload_battery_status_timer()
        interval = self._config.get_upload_battery_status_interval()
        if interval > 0:
            self._upload_battery_status_timer = LoopTimer(
                interval, self.upload_battery_status, name='upload_battery_status'
            )
            self._upload_battery_status_timer.start()

    def stop_upload_battery_status_timer(self):
        if self._upload_battery_status_timer:
            self._upload_battery_status_timer.cancel()
        self._upload_battery_status_timer = None

    def is_system_state_idle(self):
        return self._srp_wrapper.get_sys_state() == main_pb2.SystemState.SYS_STATE_IDLE
