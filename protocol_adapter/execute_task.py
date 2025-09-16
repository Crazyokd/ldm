import asyncio
import logging
import json
import math
import threading
from threading import Timer
from functools import wraps

from protocol_adapter.config import Config
from protocol_adapter.huawei_model.smt_info import SmtInfo, SmtState
from protocol_adapter.lem_report.const import AutoCheckAction
from protocol_adapter.models.task import TaskState, TaskItem, TaskType
from protocol_adapter.huawei_model.const import *
from protocol_adapter.huawei_model.const import LockSpaceType, LockSpaceRspError, ShelfAnglePolicy
from protocol_adapter.protobuf_wrapper import main_pb2
from protocol_adapter.protobuf_wrapper.path import Direction, PathType, Path
from protocol_adapter.const import ActionID, ErrorCode, ConfigKey
from protocol_adapter.path_admin import PathAdmin
from protocol_adapter.server_wrapper import ServerWrapper
from protocol_adapter.srp_wrapper import SrpWrapper
from protocol_adapter.utils import ScheduleTask, AngleUtils, GeometryUtils, MiscUtils

_logger = logging.getLogger(__name__)


class ExecuteTask:
    """
    @describe:  执行移动和动作任务的工作线程,主线程解析获取到任务数据后，委托当前class执行实际工作任务
    由于在执行移动任务或动作任务时，可能会阻塞等待执行结果，从而避免主线程卡死
    """

    def __init__(
        self,
        config: Config,
        srp_wrapper: SrpWrapper,
        server_wrapper: ServerWrapper,
        protocol,
        adapter,
    ):
        self._loop = asyncio.new_event_loop()

        self._adapter = adapter
        self._protocol = protocol

        self._server_wrapper = server_wrapper

        self._srp_wrapper = srp_wrapper
        self._srp_wrapper.add_action_task_finish_callback(self._on_action_task_finish)
        self._srp_wrapper.add_move_task_finish_callback(self._on_move_task_finish)
        self._srp_wrapper.add_dmcode_changed_callback(self._on_dmcode_changed)
        self._srp_wrapper.add_system_state_callback(self._on_system_state_changed)

        self._config = config
        self._path_admin = PathAdmin()

        self._cur_execute_task = None
        self._is_task_executing = False  # 记录任务是否在执行中

        # 正在处理中，此时即使接收到任务，也应该忽略，否则会出现上一段路径发给车，车状态还未变化时，继续接收到系统任务发给车，
        # 导致在执行任务过程中又发送了一条任务导致报错
        self._is_processing = False

        # 任务是否已经被取消了
        self._is_task_cancel = False

        # self._mutex_lock = threading.Lock()

        self._seq = 0
        self._wait_seq = 0  # 等待回复的seq

        self._detect_shelf_angle = 0  # 探测到的货架的世界坐标系角度 deg
        self._detect_shelf_sn = ''  # 探测到的货架id
        self._cur_dmcode_sn = ''  # 记录当前扫到的二维码
        self._last_shelf_sn = ''  # 最后一次成功探测到的货架码
        self._last_dmcode_sn = ''  # 最后一次成功探测到的地码

        self._is_replace_path = False  # 是否是追加路径

        self._async_lock = asyncio.Lock()  # 携程加锁

        self._move_no = 1
        self._action_no = 10000
        self._move_paths = []
        self._cur_move_path = None  # 当前正在执行的移动任务
        self._cur_path_no = 0  # 当前车辆在哪条路上
        self._task_result = main_pb2.TaskResult.TASK_RESULT_NA  # 移动任务和动作任务执行结果
        self._task_result_code = 0  # 移动任务和动作任务执行结果的值，或是错误码
        self._task_result_str = ''  # 动作任务结果的字符串

        # 货架腿对接的移动任务信息：原始目标点，结束目标点，任务 id
        self._task_identity_shelf_leg = {}

        self._is_sync_rotate_on = False
        self._shelf_angle_before_sync_rotate = None
        self._robot_pose_before_sync_rotate = None

        # 锁空间类型，移动旋转、带货架导航前旋转货架、导航到目的点后旋转货架
        self._req_space_type = REQ_SPACE_NONE
        self._lock_space_error_code = 0  # 用于状态上报

        self._path_tangent_slope = None  # 圆弧路径切线斜率，即上一条直线路径切线斜率

        self._lock_space_requester = None
        self._unlock_space_requester = None

        self._charge_timer = None
        self.send_charge_cmd_before_send_stop = False
        self.resend_charge_cmd_time = 0

        self.changed_map_response = False

        self.security_pose = None

        self._retry_arm_task = False

        self.stop_distance = 1000

        def start_loop(loop=self._loop):
            asyncio.set_event_loop(loop)
            try:
                loop.run_forever()
            finally:
                for task in asyncio.all_tasks(loop):
                    task.cancel()
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()

        self._thread = threading.Thread(target=start_loop, name='ExecuteTask')
        self._thread.start()

    def stop(self):
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=1)

    def update_scurity_pose(self):
        self.security_pose = self._srp_wrapper.get_cur_pose()

    def check_cur_pose_valid(self):
        if self.security_pose is None:
            return True
        if (
            self._srp_wrapper.is_location_democode()
            and self._srp_wrapper.get_sys_state() != main_pb2.SystemState.SYS_STATE_IDLE
            and self._cur_execute_task
            and self._cur_execute_task.is_task_linear_move()
        ):
            cur_pose = self._srp_wrapper.get_cur_pose()
            security_dist = 4000
            dist = 0
            dist_x = cur_pose['x'] - self.security_pose['x']
            dist_y = cur_pose['y'] - self.security_pose['y']
            if abs(dist_x) < 100 or abs(dist_y) < 100:
                dist = (dist_x**2 + dist_y**2) ** 0.5
            else:
                dist = abs(dist_x) + abs(dist_y)
            if dist >= security_dist:
                _logger.info(f'dist to security_pose: {dist:.3f}')
                return False
        return True

    def _run_coroutine_threadsafe(func):
        @wraps(func)
        def run(self, *args, **kwargs):
            asyncio.run_coroutine_threadsafe(func(self, *args, **kwargs), self._loop)

        return run

    def _clear_before_start_task(self) -> None:
        """
        启动一个华为任务前，需要清除上一个任务缓存的状态
        :return:
        """
        self._lock_space_error_code = 0
        self._task_result = main_pb2.TaskResult.TASK_RESULT_NA
        self._task_result_code = 0
        self._task_result_str = ''
        self.send_charge_cmd_before_send_stop = False
        self.resend_charge_cmd_time = 0
        self.stop_space_requesters()

    def get_pose_info(self) -> str:
        cur_pose = self._srp_wrapper.get_cur_pose()
        plate_angle = self._srp_wrapper.get_shelf_angle_in_global(limit=ANGLE_180)
        return (
            f'({cur_pose["x"] / 1000:.3f}, {cur_pose["y"] / 1000:.3f}, '
            f'{cur_pose["angle"] / 1000:.3f}) {plate_angle:.3f}°'
        )

    @_run_coroutine_threadsafe
    async def start(self, task):
        self._clear_before_start_task()

        if self.is_task_processing():
            _logger.warning('task is processing, wait')
            return

        _logger.info(f'task <{task.task_type.name}> start at: {self.get_pose_info()}')
        self._is_processing = True

        try:
            task_move = False
            if task.is_task_type_multi_move_after_put_shelf():
                paths_list = await self._calculate_move_path(task)
                if paths_list:
                    task_move = True
            if (
                task.is_task_linear_move()
                or task.is_task_type_smt_move()
                or task.is_task_arc_move()
                or task.is_task_type_slam_nav()
                or task.is_task_type_nopyload_multi_path_move()
                or task.is_task_type_multi_move_after_raise_shelf()
                or task.is_task_type_arm_action()
                or task.is_task_type_fork_action()
                or task_move
            ):
                # 停止充电任务不需要计算路径，避免由于位置偏差引起旋转
                if task.is_stop_charge():
                    _logger.info('Stop task')
                    if self._srp_wrapper.is_charging():
                        self.stop_charge()
                        self.reset_task_state()
                else:
                    # 同步避障参数
                    (
                        server_stop_forward,
                        server_stop_backward,
                        server_stop_left,
                        server_stop_right,
                    ) = task.get_stop_oba_params()
                    server_stop_forward += 90
                    if (
                        task.is_enable_server_oba_policy()
                        and self.stop_distance != server_stop_forward
                        and server_stop_forward >= 190
                    ):
                        _logger.info(
                            f'server oba enabled: '
                            f'stop_forward: {server_stop_forward}, '
                            f'stop_backward: {server_stop_backward}'
                        )
                        self.stop_distance = server_stop_forward
                        configs = [
                            {
                                'key': ConfigKey.STOP_DISTANCE,
                                'value': str(server_stop_forward / 1000),
                            }
                        ]
                        self._srp_wrapper.set_sros_cache_configs(configs)

                    await self._do_move_task(task)
            elif task.is_task_type_smt_action():
                if self._config.is_device_smt():
                    self._do_smt_action_task(task)
                elif self._config.is_device_aging():
                    self._do_aging_action_task(task)
            elif task.is_task_type_shelf():  # 货架任务, 包括单独举升放下货架
                await self._do_shelf_task(task)
            elif task.is_task_type_roller():  # 辊筒任务
                self._do_roller_task(task)
            else:
                _logger.warning('Unsupport task type')

        except BaseException as e:
            # NOTE: 此处异常后 _is_task_executing 有可能未重置，会导致小车状态与 ldm 上报状态不一致
            _logger.error(e, exc_info=True)
        finally:
            self._is_processing = False

    @_run_coroutine_threadsafe
    async def do_async_action(self, id, param0, param1):
        """放到独立线程排队执行动作"""
        _logger.info('do async action')

        # 虽然上一个动作已经结束，但状态同步可能有延迟，需要主动同步状态
        self._srp_wrapper.sync_robot_state()

        # 在顶升状态再次执行顶升会先放下货架然后再次顶升
        if (
            id == 4
            and (param0 in (1, 5) or (param0 == 11 and param1 > 0))
            and self._srp_wrapper.is_load_full()
        ):
            _logger.info('is load full, not raise again')
            return

        if not self._do_execute_action(id, param0, param1):
            _logger.info('do release task failed')

    def stop_space_requesters(self):
        if self._lock_space_requester:
            self._lock_space_requester.stop()
        if self._unlock_space_requester:
            self._unlock_space_requester.stop()

    @_run_coroutine_threadsafe
    async def cancel_task(self, need_put_self=True, reset_current_task=True):
        self._lock_space_error_code = 0
        self._is_task_cancel = True
        try:
            if (
                need_put_self
                and self._config.is_device_riser_rotate()
                and self._srp_wrapper.is_load_full()
            ):
                self._do_put_shelf()
        except BaseException as e:
            _logger.error(e, exc_info=True)

        self.reset_task_state(reset_current_task)
        self._reset_task_in_adapter()

    @_run_coroutine_threadsafe
    async def changed_map(self, dat):
        self._is_processing = True
        try:
            new_map_name = dat['dmcode_type']
            current_map_name = self._srp_wrapper.get_location_map_name()
            _logger.info(f'map switch: {current_map_name} -> {new_map_name}')
            if current_map_name == new_map_name:
                _logger.info('ignore switch map request: same map name')
                return

            angle_in_new_map = self._srp_wrapper.get_cur_angle() - dat['angle_offset']
            angle_in_new_map_base90 = AngleUtils.to_90n(angle_in_new_map)
            new_map_pose = {
                'x': dat['x'],
                'y': dat['y'],
                'angle': angle_in_new_map_base90 * 1000,
            }
            _logger.info(f'angle_in_new_map: {angle_in_new_map_base90}° ({angle_in_new_map})')

            # 等待定位成功
            # NOTE: 第一次使用新地图时，会进行地图生成，定位成功可能需要几分钟(视地图大小而定)
            #   因定位未成功，退出切地图逻辑也会导致小车不出梯，这里就一直等到定位成功吧
            count = 0
            while True:
                count += 1
                _logger.info(f'wait location, count: {count}')
                result = self._srp_wrapper.start_location(
                    new_map_name,
                    dat['x'],
                    dat['y'],
                    angle_in_new_map_base90,
                    dat['x_factor'],
                    dat['y_factor'],
                    True,
                )
                if result:
                    break

                await asyncio.sleep(1)

            # 等系统状态, 3s后再接任务，否则可能会导致定位未成功前给系统上报了错误的位姿/角度
            # 导致系统下发的任务角度错误
            await asyncio.sleep(3)
            self._srp_wrapper.sync_robot_state()

            # 校验定位后坐标
            cur_pose = self._srp_wrapper.get_cur_pose()
            _logger.info(f'cur position in new map: {cur_pose}')

            # 角度误差 30度，dx, dy 都在 30cm 内，认为校验通过
            if not GeometryUtils.is_same_pose(
                cur_pose, new_map_pose, threshold=300, threshold_angle=30
            ):
                _logger.error('Locate pose not match')
                # TODO: zz: matrix 切成了，但是ldm端不离开旧地图？
                return
            else:
                _logger.info('Locate pose match')

            async def goodbye_to_old_server_on_post_switch(old_server):
                # 需要给旧服务器发送离开通知
                self.changed_map_response = False
                for ct in range(0, 4000):
                    _logger.info(f'good bye to old server {old_server}, count: {ct}')

                    notify_dat = self._protocol.pack_notify_changed_map(
                        self._config.get_robot_id(), self._server_wrapper.get_msg_sn()
                    )
                    self._server_wrapper.send_request(notify_dat, server=old_server)

                    async def debug_auto_dump_netflow(time_s):
                        path = f'/sros/log/debug_map_switch_{time_s}s.pcap'
                        p = MiscUtils.run_cmd(f'tcpdump -i eth0 -w {path} udp')
                        await asyncio.sleep(time_s)
                        p.terminate()
                        _logger.warning('terminate tcpdump')

                    # DEBUG: 自动抓包调试
                    if ct > 10:
                        _logger.warning(f'still no response for the goodbye: {notify_dat.hex()}')
                        if ct == 12:
                            asyncio.create_task(debug_auto_dump_netflow(120))

                    for _ in range(5):
                        await asyncio.sleep(0.25)
                        if self.changed_map_response:
                            return

            # TODO: (zz) 切地图注册逻辑:
            # 1. 如果前后服务器没变，只需要确认向旧地图发 0x31A 并收到回复即可
            # 2. 如果前后服务器变了，需要向新 ip 注册设备成功后，再跟旧服务器发 0x31A (待处理)
            # 其它说明:
            # 1. 目前日志没发现切地图时有 ip 变动的情况
            # 2. 代码中 changed_map_response 并非只在 0x31B 回复时被更新(可能有问题)，但目前看到的日志里，
            #   都是在收到这个回复后才收到其它任务
            old_server = self._server_wrapper.get_server()
            self._server_wrapper.set_server((dat['ipv4'], dat['port']))
            await goodbye_to_old_server_on_post_switch(old_server)

        except BaseException as e:
            _logger.error(e, exc_info=True)
        finally:
            self._is_processing = False

    @_run_coroutine_threadsafe
    async def changed_switch(self, dat):
        self._is_processing = True
        try:
            cur_pose = self._srp_wrapper.get_cur_pose()
            _logger.info(f'location is start cur pose is {cur_pose}')
            if dat['x'] == 0:
                _map_name_2 = 'AC'
                if abs(57348 - cur_pose['x']) > abs(56358 - cur_pose['x']):
                    if cur_pose['angle'] > 0:
                        pose = {'x': 56358, 'y': 30083, 'angle': 90}
                    else:
                        pose = {'x': 56358, 'y': 30083, 'angle': -90}
                    # pose = {"x": 56358, "y": 30083, "angle": -90}
                else:
                    if cur_pose['angle'] > 0:
                        pose = {'x': 57348, 'y': 30083, 'angle': 90}
                    else:
                        pose = {'x': 57348, 'y': 30083, 'angle': -90}
                    # pose = {"x": 57348, "y": 30083, "angle": -90}
                for count in range(0, 5):
                    _logger.info(f'changed dmcode try location map time: {count}')
                    result = self._srp_wrapper.start_location(
                        _map_name_2, pose['x'], pose['y'], pose['angle'], absolute_location=True
                    )
                    if result:
                        break

            else:
                # TODO 切换地图需要重新定位，但是不知道地图名称
                # 等待定位成功
                _map_name_slam = 'HONOR_B5_3F_slam'
                if dat['x'] not in [56358, 57348]:
                    return
                for count in range(0, 5):
                    _logger.info(f'$$$$$$$$$changed switch try location map time: {count}')
                    result = self._srp_wrapper.start_location(
                        _map_name_slam,
                        dat['x'],
                        dat['y'],
                        dat['angle'] / 1000,
                        absolute_location=True,
                    )
                    if result:
                        break

                # 等系统状态
            await asyncio.sleep(
                3
            )  # 等待3s后再接收任务，否则可能会导致定位未成功前给系统上报了错误的位姿/角度导致系统下发的任务角度错误
            self._srp_wrapper.sync_robot_state()

            # 校验定位后坐标
            cur_pose = self._srp_wrapper.get_cur_pose()
            _logger.info(f'location in new switch after locate, cur pose is {cur_pose}')

        except BaseException as e:
            _logger.error(e, exc_info=True)
        finally:
            self._is_processing = False

    @_run_coroutine_threadsafe
    async def force_shelf_action(self, action_type, height):
        _logger.info(f'Force shelf action: {action_type} {height}')
        if height < 0:
            return

        if height > MAX_RAISE_HEIGHT:
            height = MAX_RAISE_HEIGHT

        if action_type == SHELF_FORCE_RAISE:
            if not self._do_execute_action(4, 11, height):
                _logger.error('Failed to raise shelf by force')
            else:
                _logger.info('Force raise shelf Okay')
        elif action_type == SHELF_FORCE_PUT:
            if not self._do_put_shelf():
                _logger.error('Failed to put shelf by force')
            else:
                _logger.info('Force Put shelf Okay')

    # 任务响应过程，在任务交给真正的线程后马上设置为False
    def is_task_processing(self):
        # TODO 考虑到性能，暂时先不加锁
        # self._mutex_locker.acquire()
        # processing = self._is_processing
        # self._mutex_locker.release()
        return self._is_processing

    def has_rotate_path(self):
        return self._path_admin.has_rotate_path_group()

    def get_lock_space_error_code(self):
        return self._lock_space_error_code

    # 确实等待任务执行完成才会设置为False
    def is_cur_task_running(self):
        return self._is_task_executing
        # return self._move_paths is not None and len(self._move_paths) > 0 and self._cur_move_path is not None

    # 是否正在等待当前任务完成，以解决:
    # 1 有时候接收到两个完成相同的任务（举升或下发货架），但是任务去重时比较结果却是返回false
    # 2 解决移动结束时，由于增加了旋转调整，此时接收到旋转路径导致执行失败触发路径替换小车一直旋转停不下来
    def is_waiting_cur_task_finish(self):
        if self._cur_execute_task is None:
            return False

        # 有时候接收到两个完成相同的任务（举升或下发货架），但是任务去重时比较结果却是返回false
        if self._cur_execute_task.is_task_action() and self.is_cur_task_running():
            return True

        # 解决移动结束时，由于增加了旋转调整，此时接收到旋转路径导致执行失败触发路径替换小车一直旋转停不下来
        cur_path = self._get_cur_move_path()
        if (
            self._cur_execute_task.is_task_movement()
            and cur_path
            and cur_path.type == PathType.PATH_ROTATE
        ):
            return True

        # 担心在执行动作任务时，接收到移动任务会导致风险，故在执行动作任务时，等待完成
        return self._srp_wrapper.is_executing_action()

    def has_pending_path(self):
        if self._move_paths is None:
            return False
        return len(self._move_paths) > 0

    def get_detect_shelf_sn(self):
        return self._detect_shelf_sn

    def get_detect_shelf_angle(self):
        return self._detect_shelf_angle

    def is_execute_raise_shelf_task(self) -> bool:
        return self._cur_execute_task is not None and self._cur_execute_task.is_task_raise_shelf()

    def is_execute_raise_shelf_task_failed(self) -> bool:
        """
        判断是否顶升货架失败
        :return: 是否失败
        """
        return (
            self._task_result == main_pb2.TASK_RESULT_FAILED
            and self._cur_execute_task is not None
            and self._cur_execute_task.is_task_raise_shelf()
        )

    def is_execute_detect_shelf_task_failed(self) -> bool:
        return (
            self._task_result == main_pb2.TASK_RESULT_FAILED
            and self._cur_execute_task is not None
            and self._cur_execute_task.is_task_type_shelf_sn_detect()
        )

    def is_execute_roller_task_failed(self) -> bool:
        return (
            self._task_result == main_pb2.TASK_RESULT_FAILED
            and self._cur_execute_task is not None
            and self._cur_execute_task.is_task_type_roller()
        )

    def is_execute_arm_task_failed(self) -> bool:
        return (
            self._task_result == main_pb2.TASK_RESULT_FAILED
            and self._cur_execute_task is not None
            and self._cur_execute_task.is_task_type_arm_action()
        )

    def is_retry_arm_task(self) -> bool:
        return self._retry_arm_task

    def get_raw_sros_task_result_code(self) -> int:
        """
        获取SROS执行任务的结果
        """
        return self._task_result_code

    def is_move_task(self) -> bool:
        task = self._cur_execute_task
        return task is not None and (
            task.is_task_linear_move()
            or task.is_task_arc_move()
            or task.is_task_type_slam_nav()
            or task.is_task_type_nopyload_multi_path_move()
            or task.is_task_type_multi_move_after_raise_shelf()
            or task.is_task_type_with_multi_path_move()
        )

    # 由于需要根据当前任务上报状态，个别场景可能需要保留_cur_execute_task
    def reset_task_state(self, reset_current_task=True):
        _logger.info('reset task state')
        self._path_admin.clear()
        if reset_current_task:
            self._cur_execute_task = None
        self._move_paths = []
        self._shelf_angle_before_sync_rotate = None
        self._robot_pose_before_sync_rotate = None
        self._is_task_executing = False
        self._is_task_cancel = True
        self._is_processing = False
        self._set_cur_move_path(None)
        self.stop_space_requesters()

    def _reset_task_in_adapter(self):
        self._adapter.clear_current_task()

    def may_replace_last_line(self, dst_x, dst_y):
        """目标点在最后一条直线路径内或者其延长线上"""
        last_path = self._path_admin.get_last_path()
        return (
            last_path
            and last_path.type == PathType.PATH_LINE
            and (
                last_path.is_inner_point(dst_x, dst_y)
                or last_path.is_point_on_the_extending_line(dst_x, dst_y)
            )
        )

    def handle_pre_mark_for_identity_shelf_leg(self, task):
        # 货架腿对接后续任务目标点替换
        if (
            self._task_identity_shelf_leg
            and task.task_id == self._task_identity_shelf_leg.get('task_id')
            and task.task_type in (TaskType.Shelf_SN_Detect, TaskType.Raise_Shelf_Action)
        ):
            ref_end = self._task_identity_shelf_leg.get('end')
            ref_target = self._task_identity_shelf_leg.get('target')

            move_target = task.get_move_target()
            cur_pose = self._srp_wrapper.get_cur_pose()

            if (  # 安全检查：两个目标点位置一致，前后座标 5cm 内，原移动距离 50cm 内
                ref_end
                and GeometryUtils.is_same_pose(
                    ref_target, move_target, threshold=10, ignore_angle=True
                )
                and GeometryUtils.is_same_pose(ref_end, cur_pose, threshold=50, ignore_angle=True)
                and GeometryUtils.is_same_pose(
                    cur_pose, move_target, threshold=500, ignore_angle=True
                )
            ):
                task.move_target.x = ref_end['x']
                task.move_target.y = ref_end['y']

                distance = GeometryUtils.calculate_distance(
                    move_target['x'], move_target['y'], cur_pose['x'], cur_pose['y']
                )
                _logger.info(f'替换货架腿对接后续动作目标点，偏差 {distance / 1000:.3f}m')

        else:
            self._task_identity_shelf_leg = {}

    def handle_post_mark_for_identity_shelf_leg(self):
        # 记录货架腿对接的移动任务结束位置信息
        if (
            self._cur_execute_task
            and self._cur_execute_task.state == TaskState.DONE
            and self._cur_execute_task.is_auto_identify_shelf_leg()
            and (
                self._cur_execute_task.is_task_type_no_payload_linear_move()
                or self._cur_execute_task.is_task_type_nopyload_multi_path_move()
            )
        ):
            move_target = self._cur_execute_task.get_move_target()
            move_end = self._srp_wrapper.get_cur_pose()
            if (
                self._task_identity_shelf_leg
                and self._task_identity_shelf_leg.get('task_id') == self._cur_execute_task.task_id
                and self._task_identity_shelf_leg.get('target') == move_target
            ):
                self._task_identity_shelf_leg['end'] = move_end
                distance = GeometryUtils.calculate_distance(
                    move_target['x'], move_target['y'], move_end['x'], move_end['y']
                )
                _logger.info(
                    f'货架腿对接移动结束，距原目标点：{distance / 1000:.3f}m, '
                    f'对接信息：{self._task_identity_shelf_leg}'
                )

    def check_smt_move_against_load_state(self, task) -> bool:
        if (
            self._config.is_device_smt() or self._config.is_device_aging()
        ) and task.is_task_type_smt_move():
            smt_state = self._srp_wrapper.get_smt_state()
            if task.task_type == TaskType.Smt_Multi_Path_Move and smt_state.is_load_free():
                _logger.error('smt load free while the task require load')
                return False
            elif (
                task.task_type == TaskType.Multi_Path_No_Payload_Move
                and not smt_state.is_load_free()
            ):
                _logger.error('smt not load free but the task is no payload move')
                return False
        return True

    # 移动任务
    async def _do_move_task(self, task):
        if task.is_task_type_fork_action():
            self._cur_execute_task = task
            self._do_move_task_finish()
            return

        if not self._srp_wrapper.is_system_idle():
            _logger.info('Replace move path')
            self._set_replace_path(True)
        else:
            _logger.info('New movement task, move follow path')
            self._set_replace_path(False)

        self.handle_pre_mark_for_identity_shelf_leg(task)

        if (
            task.is_task_type_with_multi_path_move()
            and self._path_admin.replace_path_if_in_one_line(task.move_target.x, task.move_target.y)
            and self.is_replace_path()
        ):
            self._move_paths = self._path_admin.get_all()
            if self._move_paths:
                self._do_move_path(self._move_paths)
                self._set_cur_move_path(self._move_paths[-1])
                self._move_paths = []
            else:
                _logger.info('get some error, move path is noe')
            return

        # TODO 充电任务调度系统会先发导航路径到充电桩??
        paths_list = await self._calculate_move_path(task)
        if (not paths_list) and task.is_start_charge():
            cur_pos = self._srp_wrapper.get_cur_pose()
            paths_list = task.calculate_adjust_line_path(cur_pos)
        if not paths_list:
            self._cur_execute_task = task

            # 如果无路径时，发现任务状态已经异常，直接退出执行流程，避免后续检查报不相干异常
            if task.state != TaskState.NONE:
                return

            # 接收到的任务只有货架角度发生变化，此时需要旋转货架
            if (
                self._config.is_device_riser_rotate()
                and self._srp_wrapper.is_load_full()
                and task.is_task_type_move_after_raise_shelf()
                and self._adjust_shelf_at_destination(task)
            ):
                _logger.info('adjust shelf angle')
                self._is_task_executing = True
                return

            _logger.error('unable to find move path')

            # 先导航到位置点后探测货码时，计算的路径条数是0
            if (
                self._cur_execute_task.is_task_type_shelf_sn_detect()
                or self._cur_execute_task.is_task_type_arm_action()
                or self._cur_execute_task.is_task_type_fork_action()
            ):
                self._do_move_task_finish()
                return

            # 如果是替换路径方式，可能是路径过短,此时不能复位
            # 但是如果不是替换路径，此时应该复位以接收新任务
            if not self.is_replace_path():
                self.reset_task_state(False)
                self._reset_task_in_adapter()  # 复位以接收新任务
            return

        def is_in_limit_v_distance_before_risk_target(target):
            cur_pos = self._srp_wrapper.get_cur_pose()
            distance = GeometryUtils.calculate_distance(
                cur_pos['x'], cur_pos['y'], target.x, target.y
            )
            return distance < DISTANCE_TO_LIMIT_V_BEFORE_RISK_TARGET

        location_map = self._srp_wrapper.get_location_map_name()
        if (
            self._config.is_entry_lift_point(task.move_target.x, task.move_target.y, location_map)
            or task.task_detail == TaskItem.Entry_Lift
        ) and is_in_limit_v_distance_before_risk_target(task.move_target):
            task.task_detail = TaskItem.Entry_Lift
            _logger.info('is entry lift task')
            for i in range(0, len(paths_list)):
                paths_list[i].limit_v = 200
            last_path = paths_list[len(paths_list) - 1]
            if last_path.type == PathType.PATH_LINE:
                last_length = GeometryUtils.calculate_distance(
                    last_path.sx, last_path.sy, last_path.ex, last_path.ey
                )
                if last_length > 100:
                    front_ex = int((last_path.sx - last_path.ex) * 100 / last_length + last_path.ex)
                    front_ey = int((last_path.sy - last_path.ey) * 100 / last_length + last_path.ey)
                    back_ex = int((last_path.ex - last_path.sx) * 20 / last_length + last_path.ex)
                    back_ey = int(
                        (last_path.ey - last_path.sy) * 20 / last_length + last_path.ey
                    )  # 多运动2cm，扫到码会停止
                    last_path_short = Path.create_line_path(
                        front_ex,
                        front_ey,
                        back_ex,
                        back_ey,
                        direction=last_path.direction,
                        limit_v=20,
                    )
                    paths_list.append(last_path_short)
                    paths_list[len(paths_list) - 2].ex = front_ex
                    paths_list[len(paths_list) - 2].ey = front_ey

        if task.task_detail == TaskItem.ROLLER_Switch:
            _logger.info('roller control move , limit v 0.2')
            for i in range(0, len(paths_list)):
                paths_list[i].limit_v = 200

        if self.has_rotate_path() or self._path_admin.self_has_not_forward_path():
            _logger.warning('wait rotate path or not forward finish before start new path')
            return
        # todo 此处返回后adapter的cur_execute_task与此对象的不一致，会导致任务阻塞，ldm上暂定继续可解决
        if self._path_admin.has_pending_path() and (
            self._path_admin.is_rotate_path_group(paths_list)
            or self._path_admin.has_not_forward_path(paths_list)
        ):
            _logger.warning('wait current path finish before start new rotate path')
            return

        # 如果新任务是圆弧路径或上一段路径是圆弧路径，则直接追加
        if task.is_task_arc_move() or task.is_task_type_with_multi_path_move():
            # 圆弧路径替换圆弧路径
            if (
                self.is_replace_path()
                and self._cur_execute_task
                and self._cur_execute_task.is_task_arc_move()
                and self._cur_execute_task.is_same_arc_points(task.path_points)
            ):
                self._path_admin.replace(paths_list)
                _logger.info('replace arc path')
            else:
                self._path_admin.append(paths_list)
                _logger.info('append arc path')
        else:  # 新任务是直线路径
            # 弧线移动->直线移动，此时也不应该替换路径
            # 直线路径替换直线路径
            if (
                self.is_replace_path()
                and self._cur_execute_task
                and self._cur_execute_task.is_task_linear_move()
            ):
                self._path_admin.replace(paths_list)
                _logger.info('replace line path')
            else:
                self._path_admin.append(paths_list)
                _logger.info('append line or mutil path')

        # 连续发送多段路径时，此时可以认为上一段路径此时已经结束
        self._cur_execute_task = task
        self._is_task_executing = True
        self._move_paths = self._path_admin.get_all()

        # 如果是空车直线移动，且自动识别货架腿
        if (
            task.is_task_type_no_payload_linear_move()
            or task.is_task_type_nopyload_multi_path_move()
        ) and task.is_auto_identify_shelf_leg():
            if (
                self._move_paths is not None
                and self._move_paths[-1].type == PathType.PATH_LINE
                and not self._srp_wrapper.is_location_democode()
            ):  # 捕获光旋转一下也下发货架腿识别的异常
                _logger.info('append create_identify_shelf_leg_rotate_path')
                self._task_identity_shelf_leg = {
                    'task_id': task.task_id,  # 任务id
                    'target': task.get_move_target(),  # 原始目标点
                    'end': None,  # 停止位置（货架中心）
                }
                self._move_paths.append(
                    task.create_identify_shelf_leg_rotate_path(task.get_target_angle() / 1000)
                )

        move_path = self._get_cur_move_path()
        # 因为旋转路径需要等待旋转空间申请，因此旋转路径暂不考虑进行路径替换
        if move_path and not self._srp_wrapper.is_system_idle():
            # 如果上一条路径是旋转路径，也应该等旋转路径完成
            if move_path.type == PathType.PATH_ROTATE:
                _logger.info('Wait current rotate path finish before start a new Path')
                self._set_replace_path(False)
                return
        #     # 如果下一条路径是旋转路径，应该等待上一条路径走完, 如果是圆弧路径，可能第一条路径旋转调整
        #     if len(self._move_paths) > 0 and (self._move_paths[0].type == PathType.PATH_ROTATE and
        #                                       self._cur_execute_task.is_task_arc_move() is False):
        #         _logger.info("Wait for current path finish before start a new Rotate path")
        #         self._set_replace_path(False)
        #         return
        self._move_next_path()

    # 货架动作任务
    async def _do_shelf_task(self, cur_task):
        # shelf_id = self._cur_execute_task.actuator_info.id
        # raise_height = self._cur_execute_task.actuator_info.raise_height
        _logger.info('Shelf task')
        self._set_replace_path(False)

        # 继续接收到该动作任务，如果不处理系统会报错, 例如货架已经举升再发送举升货架任务
        if (
            not self._srp_wrapper.is_action_task_failed()
            and self._cur_execute_task
            and self._cur_execute_task.is_duplicated_task(cur_task)
        ):
            _logger.info('Action task is executing, ignore same action task request')
            return

        # 需要在上面代码执行后才能给_cur_execute_task赋值
        self._cur_execute_task = cur_task
        self._is_task_executing = True

        if cur_task.is_no_detect_raise():
            _logger.info('force raise shelf without detect')
            self.force_shelf_action(SHELF_FORCE_RAISE, 100)
            self.reset_task_state()
            return

        # 注意: 举升/放下货架叠加直线运动时，执行完动作后再计算路径，以免举升、放下货架后机器人路径起点(当前位置)有更新
        # !!!!!!!!举升货架叠加直线移动只是移动任务，并不是举升货架动作任务和移动任务的组合!!!!!!
        if self._cur_execute_task.is_task_type_raise_shelf_only():
            if self._config.is_device_riser_rotate():
                # 正常此时还没有货架，锁空间只针对小车本体，也存在已顶起还继续发顶升的情况
                if self._cur_execute_task.is_allow_to_rotate_plate(
                    load_full=self._srp_wrapper.is_load_full()
                ):
                    self._request_lock_space(REQ_SPACE_ADJUST_WHEN_RAISE_SHELF)
                else:
                    await self._process_raise_shelf(allow_rotate=False)
        elif self._cur_execute_task.is_task_put_shelf() and self._config.is_device_riser_rotate():
            # 先看看是否需要放下货架
            if not (
                self._cur_execute_task.is_task_type_move_after_put_shelf()
                and not self._srp_wrapper.is_load_full()
            ):
                result = self._do_put_shelf()
                if not result:
                    _logger.error('put shelf error')
                    self.reset_task_state()
                    return

            # 如果任务是仅放下货架，放下后就结束了
            if self._cur_execute_task.is_task_type_put_shelf_only():
                self.reset_task_state(False)
                return

            # 还有后续移动，继续处理

            # move_still 卡复合任务的移动，不卡放下货架
            if self._cur_execute_task.is_move_still():
                _logger.info('move still, abort on move')
                self.reset_task_state(False)
                return

            paths = await self._calculate_move_path(self._cur_execute_task)
            if paths is None or len(paths) <= 0:
                _logger.error('unable to find move path')
                self.reset_task_state(False)
                return
            _logger.info(f'device move total path number: {len(paths)}')
            self._path_admin.clear()
            self._path_admin.append(paths)
            self._move_paths = self._path_admin.get_all()
            self._move_next_path()

    def _do_smt_adjust_height_and_width(self, task, is_async=False):
        if not (self._config.is_device_smt() and task.is_task_type_smt()):
            return

        # 与当前 smt 工装状态比较
        smt_state = self._srp_wrapper.get_smt_state()

        # 因为任务类型共用，调度下发的可能不带 smt 车的结构体信息，这里不要触发异常
        if not (isinstance(smt_state, SmtState) and isinstance(task.actuator_info, SmtInfo)):
            _logger.warning('no valid smt state!')
            return

        do_action = self.do_async_action if is_async else self._do_execute_action

        # TODO(zZ): 多工装组调高调宽支持
        for i in range(task.actuator_info.unit_ct):
            unit_this = task.actuator_info.units[i]
            unit_ref = smt_state.units[i]
            if unit_this.index == unit_ref.index:
                # 先调宽再调高(根据货物类型调宽)
                if unit_this.cargo_type != unit_ref.cargo_type:
                    _logger.info(
                        f'smt adjust width: {unit_ref.cargo_type} -> {unit_this.cargo_type}'
                    )
                    do_action(ActionID.EAC, 22, unit_this.cargo_type)
                if unit_this.lift_height != unit_ref.lift_height:
                    _logger.info(
                        f'smt adjust lift height: {unit_ref.lift_height} -> {unit_this.lift_height}'
                    )
                    do_action(ActionID.EAC, 21, unit_this.lift_height)

    def _do_aging_adjust_height_and_width(self, task, is_async=False):
        if not (self._config.is_device_aging() and task.is_task_type_smt()):
            return

        if not isinstance(task.actuator_info, SmtInfo):
            return

        do_action = self.do_async_action if is_async else self._do_execute_action
        unit_this = task.actuator_info.units[0]
        do_action(ActionID.EAC, 3, unit_this.cargo_type)
        do_action(ActionID.EAC, 7, unit_this.lift_height)

    def _do_smt_action_task(self, cur_task):
        # 校验动作位置是否一致
        cur_pose = self._srp_wrapper.get_cur_pose()
        move_target = cur_task.get_move_target()
        if not GeometryUtils.is_same_pose(cur_pose, move_target, threshold=50, threshold_angle=5):
            _logger.error(f'动作执行位置不匹配: cur: {cur_pose}, target: {move_target}')
            return

        self._cur_execute_task = cur_task
        self._is_task_executing = True

        assert isinstance(cur_task.actuator_info, SmtInfo)
        unit = cur_task.actuator_info.units[0]
        if unit.action_direction == SmtActionDirection.Left:
            load_param0 = 1
            dock_param1 = 1
        elif unit.action_direction == SmtActionDirection.Right:
            load_param0 = 2
            dock_param1 = 2
        else:
            _logger.error('未定义的动作方向')
            return

        # 执行上下料时先确保调高调宽与目标一致
        self._do_smt_adjust_height_and_width(cur_task)
        result = False
        load_param1 = 0

        smt_state = self._srp_wrapper.get_smt_state()
        cargo_state = smt_state.units[0].cargo_state

        # 上下料过程(仅在载货状态符合预期时执行)：
        # 搭桥伸出: 192.204.2  (不需要指定长度)
        # 上料：192.2.3  履带转动，把料送到搭桥中心
        # 搭桥收回：192.205.0
        if cur_task.task_type == TaskType.Smt_Load_Action:
            if cargo_state == 0:
                result = True
                load_param1 = 3
            else:
                _logger.warning(f'smt 载货任务异常，当前状态: cargo_state={cargo_state}')

        elif cur_task.task_type == TaskType.Smt_Unload_Action:
            if cargo_state == 1:
                result = True
                load_param1 = 4
            else:
                _logger.warning(f'smt 卸货任务异常，当前状态: cargo_state={cargo_state}')

        # 取/放 货流程: 高精度对接 - 搭桥伸出 - 取/放 - 搭桥归位
        if result:
            result = self._do_execute_action(136, 2, 0)  # 启用高精度对接
        if result:
            result = self._do_execute_action(ActionID.EAC, 204, dock_param1)
        if result:
            assert load_param1 in (3, 4)
            result = self._do_execute_action(ActionID.EAC, load_param0, load_param1)
        if result:
            result = self._do_execute_action(ActionID.EAC, 205, 0)

        if result:
            self._cur_execute_task.state = TaskState.DONE
        else:
            _logger.error('动作失败')

        self._is_task_executing = False

    def _do_aging_action_task(self, cur_task):
        """执行老化工装动作任务"""
        # 校验动作位置是否一致
        cur_pose = self._srp_wrapper.get_cur_pose()
        move_target = cur_task.get_move_target()
        if not GeometryUtils.is_same_pose(cur_pose, move_target, threshold=50, threshold_angle=5):
            _logger.error(f'动作执行位置不匹配: cur: {cur_pose}, target: {move_target}')
            return

        _logger.info('start do aging task')
        self._cur_execute_task = cur_task
        self._is_task_executing = True

        assert isinstance(cur_task.actuator_info, SmtInfo)
        unit = cur_task.actuator_info.units[0]

        # 按要求调高调宽
        self._do_aging_adjust_height_and_width(cur_task)
        # 高精度对接？
        result = self._do_execute_action(136, 2, 0)  # 启用高精度对接
        if result:
            # 前阻挡去原位
            result = self._do_execute_action(ActionID.EAC, 5, 2)
        if result:
            # 上料/下料
            result = self._do_execute_action(ActionID.EAC, 1, unit.action_type)
        # 前阻挡去工作位
        if result:
            result = self._do_execute_action(ActionID.EAC, 5, 1)
        else:
            _logger.error('动作执行失败')

        self._is_task_executing = False

    # 滚筒任务
    def _do_roller_task(self, cur_task):
        _logger.info('Roller task')
        self._cur_execute_task = cur_task
        self._is_task_executing = True

        actuator_info = self._cur_execute_task.actuator_info
        if actuator_info is None:
            _logger.error('Actuator info is invalid when execute roller action')
            return
        for idx, action_info in enumerate(actuator_info):
            if not action_info.is_valid():
                continue
            if idx == 0:
                if not self._do_roller_action(idx, action_info.action_type, action_info.direction):
                    _logger.error('failed to execute roller action')
                break
            else:
                if not self._do_roller_action(idx, action_info.action_type, action_info.direction):
                    _logger.error('failed to execute roller action')
        self._is_task_executing = False

    def _on_move_task_finish(self, move_task):
        asyncio.run_coroutine_threadsafe(self._process_move_task_finish(move_task), self._loop)

    def _on_dmcode_changed(self, dmcode_sn):
        if self._cur_dmcode_sn != dmcode_sn:
            self._cur_dmcode_sn = dmcode_sn

    def _on_system_state_changed(self, system_state):
        pass

    async def _process_move_task_finish(self, move_task):
        self._set_replace_path(False)
        # todo同步状态也无法保证系统状态是同步的，可以一定程度减少任务结束，系统状态没有即时同步的情况
        self._srp_wrapper.sync_robot_state()
        if self._cur_execute_task is None:
            return

        # TODO 可能收到多次notify
        if self._move_no != move_task.no:
            _logger.warning(f'move task num unmatch: wait {self._move_no}, receive {move_task.no}')
            return

        # 更新值，不再接收同一个no下一个notify
        cur_pos = self._srp_wrapper.get_cur_pose()
        _logger.info(f']]]]] cur move task {self._move_no} finished, {self.get_pose_info()}')
        self._move_no += 1
        result = move_task.result

        move_path = self._get_cur_move_path()
        if move_path is None:
            _logger.info('cur move path is none')
            self._move_next_path()
            return
        _logger.info(f'move finished with: {move_path.type.name}')
        if move_path.type == PathType.PATH_ROTATE:
            if self._cur_execute_task.is_task_type_move_after_raise_shelf():
                self._display_shelf_angle('After rotate path')

            # 旋转顶升机构需先执行顶升，然后开启同步旋转，将车转到系统发送角度，最后关闭同步旋转
            if self._cur_execute_task.is_task_type_raise_shelf_only():
                _logger.info('Rotate after raise shelf OKAY')

            # 如果当前是旋转路径，则释放空间，不需要等待空间释放完成，继续下一个任务
            if move_path.req_lock_space:
                _logger.info('will unlock')
                self._request_unlock_space(cur_pos)

            # 关闭同步旋转
            # TODO 等待关闭同步旋转完成???
            if self._is_sync_rotate_on:
                # 注意:耗时操作会卡住thread
                _logger.info('is sync')
                if not self._do_sync_rotate_action(False):
                    _logger.error('failed to close sync rotate')
                    return

                # 关同旋转时校准货架
                # 如果是货架腿自动识别，当前举升货架位置和系统发送的举升货架位置距离偏差超过阈值时
                # 需要旋转小车并移动到系统指定位置，此时是短距离移动调整，不宜将将货架摆成与车平行
                # 或垂直方向（调整角度过大，位置空间可能很小），只在最后一段旋转路径后才进行货架调整
                _logger.info('adjust shelf on sync rotate off')
                self._adjust_shelf_angle()
        elif self._cur_execute_task.is_task_type_raise_shelf_only() and not self._move_paths:
            _logger.info('ajust shelf after raise shelf')
            self._adjust_shelf_angle()

        if result == main_pb2.TASK_RESULT_OK:
            # self._set_cur_move_path(None)

            # 举升货架叠加直线移动，导航到目标点后需要调整货架角度
            # 只处理单独接收到旋转货架任务的任务，先导航后旋转货架的任务先不处理
            # TODO 圆弧移动接收后调整货架
            _logger.info('is ok')
            if (
                self._config.is_device_riser_rotate()
                and self._srp_wrapper.is_load_full()
                and len(self._move_paths) <= 0
                and (
                    self._cur_execute_task.is_task_type_linear_move_after_raise_shelf()
                    or self._cur_execute_task.is_task_type_multi_move_after_raise_shelf()
                )
            ):
                _logger.info('is ko')

                if not self._cur_execute_task.is_at_target_pos(cur_pos, False):
                    _logger.error('任务正常结束，但车没有到目标点！不纠正货架，停在此处')
                    self.reset_task_state(False)
                    return

                # 调整货架前，先检查调整小车方向(如果小车方向未到位， 可能导致货架角度超过限制)
                self._adjust_robot_at_destination(self._cur_execute_task)

                if self._adjust_shelf_at_destination(self._cur_execute_task):
                    _logger.info('will return')
                    return
            _logger.info('will do next')
            self._move_next_path()
        elif result == main_pb2.TASK_RESULT_FAILED:
            _logger.error(f'move task failed: {move_task.failed_code}')
            self.reset_task_state(False)
            return
        elif result == main_pb2.TASK_RESULT_CANCELED:
            self.reset_task_state(False)
            _logger.info('move task cancel')
        else:
            _logger.info('get somm error')

    def _adjust_robot_at_destination(self, task):
        # 没路径，系统空闲，有任务
        if self._move_paths or not (task and self._srp_wrapper.is_system_idle()):
            return

        if self._srp_wrapper.is_load_full() and task.is_task_type_multi_move_after_raise_shelf():
            target_angle = task.move_target.angle / 1000.0
            robot_angle = self._srp_wrapper.get_cur_angle()
            shelf_angle_to_robot = self._srp_wrapper.get_shelf_angle_to_robot()
            shelf_angle_in_global = self._srp_wrapper.get_shelf_angle_in_global()
            delta_angle = AngleUtils.delta_norm(robot_angle, target_angle)

            # 小车偏离目标角度过大时什么都不做
            if delta_angle > SHELF_ROTATE_ANGLE_THRESHOLD:
                _logger.warning(f'large robot angle delta at dest: {delta_angle:.2f}°')
                return

            # 货架实际角度稍大，相对小车角度很小，小车角度很小
            if (
                delta_angle > 1
                and AngleUtils.delta_90n(shelf_angle_to_robot) < SHELF_ROTATE_ANGLE_THRESHOLD
                and AngleUtils.delta_90n(shelf_angle_in_global) > SHELF_ROTATE_ANGLE_THRESHOLD
                and AngleUtils.delta_90n(shelf_angle_in_global)
                < SHORT_PATH_LOCKSPACE_ANGLE_THRESHOLD
            ):
                _logger.info(
                    'adjust robot before shelf, robot/shelf: '
                    f'{robot_angle:.2f}°/{shelf_angle_in_global:.2f}°'
                )

                # 先把小车转到位
                rotate_path = Path.create_rotate_path(int(math.radians(target_angle) * 1000))
                self._set_replace_path(False)
                self._path_admin.clear()
                self._path_admin.append([rotate_path])
                self._move_paths = self._path_admin.get_all()
                asyncio.run_coroutine_threadsafe(self._do_move_next_path(), self._loop)

    def _adjust_shelf_at_destination(self, task):
        """目标点调整货架，如果发现异常，可通过返回 True 结束执行流程"""
        if not self._srp_wrapper.is_system_idle():
            return False
        shelf_angle_global = self._srp_wrapper.get_shelf_angle_in_global()
        is_need_rotate = task.is_need_rotate_shelf_at_destination(shelf_angle_global)
        _logger.info(
            f'cur shelf global angle: {shelf_angle_global:.3f}°, '
            f'at target is_need_rotate: {is_need_rotate}'
        )

        if task.is_task_type_move_after_raise_shelf() and is_need_rotate:
            shelf_rotation_degrees = self._cur_execute_task.get_shelf_angle_offset_at_destination(
                shelf_angle_global
            )
            space_type_req = self._get_space_type_from_lock_type(
                REQ_SPACE_ROTATE_SHELF_AT_DESTINATION, shelf_rotation_degrees
            )
            if task.is_allow_to_rotate_with_shelf(space_type_req, shelf_rotation_degrees):
                self._request_lock_space(REQ_SPACE_ROTATE_SHELF_AT_DESTINATION, space_type_req)
            else:
                # 报角度异常，但这里要重置任务，否则后续任务进不来
                _logger.warning('目标点货架调整：需要转，但是不让转，是不是角度不对?')
                if self._cur_execute_task:
                    if shelf_rotation_degrees > 30:
                        # 需要转的角度过大时，应该是任务角度与地图约束冲突
                        self._cur_execute_task.state = TaskState.TASK_WRONG_ANGLE
                    else:
                        self._cur_execute_task.state = TaskState.SHELF_ANGLE_ERROR
                self.reset_task_state(reset_current_task=False)
            return True

        return False

    def _on_action_task_finish(self, action_task):
        pass

    async def _request_lock_space_req(self, cur_pos, space_type, length):
        _logger.info(f'device request lock space: {cur_pos}, space type: {space_type}')
        dat = self._protocol.pack_lock_space_req(
            self._config.get_robot_id(),
            self._server_wrapper.get_msg_sn(),
            cur_pos['x'],
            cur_pos['y'],
            lock_type=space_type,
            lock_width=length,
            lock_length=length,
        )
        self._server_wrapper.send_request(dat)

    def _get_space_type_from_lock_type(self, lock_type, rotate_angle: float = 0):
        """从 lock_type 获取要申请的 space_type，
        对于导航前移动，需要 rotate_angle 信息以选择更合适的锁空间类型申请
        """
        # 默认空车旋转
        space_type = LockSpaceType.NO_PAYLOAD_ROTATE

        if self._srp_wrapper.is_load_full():
            # 载货状态默认转货架
            space_type = LockSpaceType.SHELF_ROTATE

            # 导航时旋转，默认开启同步旋转，只需要转底盘，申请小车相对旋转
            if lock_type == REQ_SPACE_MOVE_ROTATE:
                space_type = LockSpaceType.RECT_ROTATE

            # 如果已顶升，考虑到货架位货架不旋转，这里应该申请小车旋转
            if lock_type == REQ_SPACE_ADJUST_WHEN_RAISE_SHELF:
                space_type = LockSpaceType.RECT_ROTATE

            # 对于转货架，如果提供了角度信息，就优先匹配小角度转货架，
            if (
                space_type == LockSpaceType.SHELF_ROTATE
                and rotate_angle > 0
                and rotate_angle < RECT_ROTATE_SMALL_ANGLE_THRESHOLD
            ):
                space_type = LockSpaceType.RECT_ROTATE

        return space_type

    def _request_lock_space(self, lock_type, space_type=LockSpaceType.NONE):
        _logger.info(f'_request_lock_space type: {lock_type}')
        self._lock_space_error_code = 0
        if lock_type == REQ_SPACE_NONE:
            _logger.info('Lock space request type is none')
            return

        cur_pos = self._srp_wrapper.get_cur_pose()
        if cur_pos is None:
            return
        self._req_space_type = lock_type

        if space_type == LockSpaceType.NONE:
            space_type = self._get_space_type_from_lock_type(lock_type)

        w, l = (0, 0)
        if space_type in (LockSpaceType.SHELF_ROTATE, LockSpaceType.RECT_ROTATE):
            w, l = self._config.get_lock_space_area()

        # 准备周期重试请求
        async def coro():
            await self._request_lock_space_req(cur_pos, space_type, max(w, l))

        async def coro_end(task=self._cur_execute_task):
            # 结束时先看是不是还是调用时的任务
            if self._cur_execute_task is task:
                self.reset_task_state(false)
                self._reset_task_in_adapter()

        if self._lock_space_requester:
            self._lock_space_requester.stop()

        self._lock_space_requester = ScheduleTask(
            coro, LOCK_SPACE_RESEND_INTERVAL * 1000, 40, coro_end=coro_end
        )
        self._lock_space_requester.start(self._loop)

    async def _request_unlock_space_req(self, unlock_pos):
        _logger.info(f'device request unlock space: {unlock_pos}')
        dat = self._protocol.pack_unlock_space_req(
            self._config.get_robot_id(),
            self._server_wrapper.get_msg_sn(),
            unlock_pos['x'],
            unlock_pos['y'],
        )
        self._server_wrapper.send_request(dat)

    def _request_unlock_space(self, unlock_pos):
        _logger.info(f'_request_unlock_space, pose: {unlock_pos}')
        if unlock_pos is None:
            return

        async def coro():
            await self._request_unlock_space_req(unlock_pos)

        self._unlock_space_requester = ScheduleTask(coro, LOCK_SPACE_RESEND_INTERVAL * 1000, 10)
        self._unlock_space_requester.start(self._loop)

    def process_lock_space_rsp(self, dat):
        asyncio.run_coroutine_threadsafe(self._do_process_lock_space_rsp(dat), self._loop)

    async def _do_process_lock_space_rsp(self, dat):
        if not self._lock_space_requester:
            return

        if not self._cur_execute_task:
            _logger.error('no cur_execute_task on lockspace resp')
            self._lock_space_requester.stop()
            self.cancel_task(need_put_self=False, reset_current_task=True)
            return

        result = self._protocol.unpack_lock_space_rsp(dat)

        self._lock_space_error_code = result['error']
        req_type = self._req_space_type  # await中可能会修改该值

        if result['result'] == RESPONSE_TRUE:
            _logger.info('Lock space is accepted')
            self._lock_space_requester.stop()  # 成功就不需要继续请求了

            # 重置异常状态: 特别是临时失败重试成功
            if self._cur_execute_task.state in (
                TaskState.LOCK_SPACE_FAILED_TEMP,
                TaskState.LOCK_SPACE_FAILED_PERMANENT,
            ):
                self._cur_execute_task.state = TaskState.NONE

            self._req_space_type = REQ_SPACE_NONE
            # 空车旋转或背货架旋转
            if req_type == REQ_SPACE_MOVE_ROTATE:
                # 如果背货架旋转,则需要判断当前货架角度和货架目标角度是否相同,如果已经相同(不需要旋转货架),则开启同步旋转
                # 旋转移动完成后再关闭同步旋转, 否则带货架一起旋转
                result = self._sync_rotate_state_before_move()
                if not result:
                    _logger.error('failed to open sync rotate before rotate path')
                    return
                await self._do_move_next_path()
            elif req_type == REQ_SPACE_ADJUST_WHEN_RAISE_SHELF:
                # 顶升货架时旋转校准
                await self._process_raise_shelf()
                # 结束后释放空间
                self._request_unlock_space(self._srp_wrapper.get_cur_pose())
            elif req_type == REQ_SPACE_ROTATE_SHELF_BEFORE_MOVE:
                # 带货架导航前旋转货架
                self._display_shelf_angle('rotate shelf before move')

                shelf_move_angle = self._cur_execute_task.get_shelf_angle_at_moving()
                if shelf_move_angle == ShelfAnglePolicy.Ignore:
                    shelf_move_angle = self._srp_wrapper.get_shelf_angle_to_robot()

                # 旋转货架
                if self._do_rotate_shelf(
                    self._srp_wrapper.get_shelf_angle_to_robot(), shelf_move_angle
                ):
                    _logger.info(
                        'rotate shelf Okay, current shelf angle: '
                        f'{self._srp_wrapper.get_shelf_angle_in_global():.3f} deg'
                    )
                    # 旋转货架结束后释放空间
                    self._request_unlock_space(self._srp_wrapper.get_cur_pose())

                    # 在举升货架后移动过程中需要调整货架角度，调整货架后移动到指定目标点
                    self._display_shelf_angle('Before move after rotate shelf')
                    await self._do_move_next_path()
            elif req_type == REQ_SPACE_ROTATE_SHELF_AT_DESTINATION:
                try:
                    # 导航到目标位置后旋转货架
                    self._display_shelf_angle('Move at target before rotate shelf')

                    # 获取目标点货架角度，忽略的话就是用当前货架角度
                    shelf_angle_at_dest = self._cur_execute_task.get_shelf_angle_at_dest()
                    if shelf_angle_at_dest == ShelfAnglePolicy.Ignore:
                        shelf_angle_at_dest = self._srp_wrapper.get_shelf_angle_in_global(
                            limit=ANGLE_180
                        )

                    target_angle = AngleUtils.normalize_360(
                        shelf_angle_at_dest - self._srp_wrapper.get_cur_angle()
                    )
                    shelf_angle_to_robot = self._srp_wrapper.get_shelf_angle_to_robot()
                    if self._do_rotate_shelf(shelf_angle_to_robot, target_angle):
                        _logger.info(
                            'rotate shelf Okay, current shelf angle: '
                            f'{self._srp_wrapper.get_shelf_angle_in_global():.3f} deg'
                        )
                        self._request_unlock_space(self._srp_wrapper.get_cur_pose())
                        self._display_shelf_angle('Move at target after rotate shelf')
                        # 导航到目标点后调整货架结束
                        self._move_next_path()
                    else:
                        _logger.info('open sync rotate okay')
                except BaseException as e:
                    _logger.error(e, exc_info=True)
        else:
            error_code = result['error']
            # 如果任务已经取消，直接返回
            if not self.is_cur_task_running():
                _logger.warning(f'lock space rejected [{error_code}] and no running task')
                self._lock_space_requester.stop()
                return

            if error_code in (
                LockSpaceRspError.FAILED_TMP_LOCKED,
                LockSpaceRspError.FAILED_TMP_ROBOT,
            ):
                _logger.warning(f'lock space rejected temporary [{error_code}], retry later')
                if self._cur_execute_task:
                    self._cur_execute_task.state = TaskState.LOCK_SPACE_FAILED_TEMP
            elif error_code >= LockSpaceRspError.FAILED_PERMANENT_INPUT_PARAMS:
                _logger.warning(f'lock space rejected permanent [{error_code}], cancel task')
                self._lock_space_requester.stop()

                if self._cur_execute_task:
                    self._cur_execute_task.state = TaskState.LOCK_SPACE_FAILED_PERMANENT

                self.cancel_task(need_put_self=False, reset_current_task=False)
            else:
                _logger.error(f'lock space rejected [{error_code} ??], stop request')
                self._lock_space_requester.stop()

                self.cancel_task(need_put_self=False, reset_current_task=False)

    async def _process_raise_shelf(self, allow_rotate=True):
        """执行顶升货架及其后的微调动作
        注意顶升前的锁空间申请检查是以空车状态为参考申请的，
        顶起货架后的大角度调整需要在移动任务前另外申请锁空间（载货状态）
        """
        self._is_task_cancel = False
        if not self._cur_execute_task.is_task_type_raise_shelf_only():
            return

        # 举升货架
        if not self._srp_wrapper.is_load_full():
            result = await self._do_process_raise_shelf(allow_rotate)
            if not result:
                _logger.error('raise shelf error')
                self.reset_task_state()  # 失败后需要复位以便进行重试(如果不复位会导致忽略相同任务)
                self._reset_task_in_adapter()
                return

        _logger.info('Raise shelf Okay!!')

        # 等待举升货架后，载货状态同步
        while True:
            if self._srp_wrapper.is_load_full():
                break
            _logger.info('wait agv update load full state')
            await asyncio.sleep(0.1)

        cur_pose = self._srp_wrapper.get_cur_pose()
        distance = self._cur_execute_task.get_distance_to_target(cur_pose)

        # 检测货架距离偏差是否超限，记录状态上报异常，超限就不必继续和调整了
        if distance > RAISE_SHELF_MAX_PATH_LENGTH_THRESHOLD:
            _logger.error(f'shelf distance too large, distance: {distance:.1f} mm')
            # 这里是在清任务状态之后更新货架偏移状态，解抱闸清空
            self.reset_task_state(reset_current_task=False)
            if self._cur_execute_task:
                self._cur_execute_task.state = TaskState.SHELF_OFFSET_ERROR
            return

        # 检测顶升结束后，到站点的偏差(角度与距离)，并主动进行微调
        paths = self._cur_execute_task.calculate_adjust_rotate_path(cur_pose)
        if not paths:
            _logger.info('no angle adjust, check for distance adjust')
            paths = self._cur_execute_task.calculate_adjust_line_path(cur_pose)

        # 是否需要微调路径以回到站点（方向偏差，距离偏差）
        if paths:  # 需要微调，直接按调整路径执行调整
            _logger.info(f'adjust robot after raise shelf, adjust path number: {len(paths)}')
            self._path_admin.clear()
            self._path_admin.append(paths)
            self._move_paths = self._path_admin.get_all()
            self._move_next_path()
        else:  # 不需要微调回站点，开始常规默认的调整货架
            _logger.info('no adjust path, adjust shelf directly')
            self._adjust_shelf_angle()
            self.reset_task_state(reset_current_task=False)

    async def _do_process_raise_shelf(self, allow_rotate=True):
        _logger.info('before raise shelf')
        self._detect_shelf_sn = ''

        # 解决货架举升校验失败后，重新搬来货架能继续执行任务
        while not self._is_task_cancel and not self._check_shelf_sn():
            _logger.error('Check shelf sn before raise shelf failed')
            await asyncio.sleep(ACTION_RETRY_TIME_GAP)

        if self._is_task_cancel or self._srp_wrapper.is_fault_error():
            _logger.info('task cancel or fault error')
            return False

        # 由于硬件反应，延时1s
        await asyncio.sleep(1)

        _logger.info('Check shelf sn before raise shelf Okay')
        return self._do_raise_shelf(allow_rotate)

    # 校验货架id
    def _check_shelf_sn(self) -> bool:
        """
        检测当前货架码和ldm下发的货架码是否一致
        :return:
        """
        result = self._do_execute_action(ActionID.DETECT_SVC, 1, 0)
        if not result:
            _logger.error('Execute detect shelf sn failed')
            return False

        # 执行完任务后在任务结束时货架码和角度自动更新了
        if self._detect_shelf_sn in ('', '-'):
            self._adapter.send_alarm(
                ALARM_CATEGORY_6,
                ALARM_CODE_NO_RECOGNIZE_SHELF_SN,
                ALARM_STATUS_PULSE,
                ALARM_GRADE_NORMAL,
            )
        check_result = self._cur_execute_task.is_shelf_sn_match(self._detect_shelf_sn)
        if not check_result:
            self._adapter.send_alarm(
                ALARM_CATEGORY_6,
                ALARM_CODE_SHELF_SN_MISMATCH,
                ALARM_STATUS_PULSE,
                ALARM_GRADE_NORMAL,
            )
        return check_result

    def _display_shelf_angle(self, where):
        angle_to_robot = self._srp_wrapper.get_shelf_angle_to_robot()
        angle_in_global = self._srp_wrapper.get_shelf_angle_in_global()
        robot_angle = self._srp_wrapper.get_cur_angle()
        _logger.info(
            f'{where}: (shelf, robot, relative) angle: '
            f'({angle_in_global:.1f}, {robot_angle:.1f}, {angle_to_robot:.1f})°'
        )

    def process_unlock_space_rsp(self, dat):
        asyncio.run_coroutine_threadsafe(self._do_process_unlock_space_rsp(dat), self._loop)

    async def _do_process_unlock_space_rsp(self, dat):
        if not self._unlock_space_requester:
            return

        result = self._protocol.unpack_lock_space_rsp(dat)
        if result['result'] == RESPONSE_TRUE:
            _logger.info('Unlock space is accepted')
            self._unlock_space_requester.stop()
            # self._move_next_path()
        else:  # 重新请求释放空间
            # 如果任务已经取消
            _logger.info('Unlock space is refused')
            if self._get_cur_move_path() is None:
                self._unlock_space_requester.stop()
                return
            self._unlock_space_requester.restart()

    def get_shelf_angle_offset_before_move(self):
        """获取移动前货架实际角度与货架期望角度的偏差"""
        if not self._cur_execute_task:
            return 0

        shelf_angle_to_robot = self._srp_wrapper.get_shelf_angle_to_robot()
        cur_diff = AngleUtils.normalize_180(shelf_angle_to_robot)  # 当前偏差角度
        dest_diff = self._cur_execute_task.get_expected_shelf_angle_to_robot_before_move(
            shelf_angle_to_robot
        )

        if dest_diff is None:  # 目标货架角度不限
            return 0

        return AngleUtils.delta_norm(cur_diff, dest_diff)

    # 执行移动路径
    def _move_next_path(self):
        _logger.info('move next path')
        if self._move_paths is None or len(self._move_paths) <= 0:
            # 如果是货架腿识别任务，导航到位后，需要顶升货架
            if self._cur_execute_task:
                # 非旋转路径才需要对角度进行校准，同时保证校准最多只执行一次，自动货架退识别不需要调整
                if (
                    self._cur_move_path
                    and self._cur_move_path.type != PathType.PATH_ROTATE
                    and not self._cur_execute_task.is_auto_identify_shelf_leg()
                ):
                    # 移动结束后,如果存在角度误差,则引入旋转路径修正角度
                    rotate_path = self._cur_execute_task.get_adjust_rotate_path(
                        self._srp_wrapper.get_cur_angle()
                    )
                    if rotate_path and not self._cur_execute_task.is_start_charge():
                        _logger.info('Add adjust rotate path')
                        # 追加的旋转路径肯定不是替换路径
                        self._set_replace_path(False)
                        self._path_admin.clear()
                        self._path_admin.append([rotate_path])
                        self._move_paths = self._path_admin.get_all()
                        self._move_next_path()
                        return
            # 如果不存在角度误差,则结束当前任务
            self._do_move_task_finish()
            return

        # 执行移动前，需要先看看是否需要申请锁空间，调整角度

        # TODO: 如果是追加路径的话，取的第一个路径可能是已经走过很久的路径，下面的判断都有问题
        path = self._move_paths[0]
        if path.type == PathType.PATH_ROTATE:  # 旋转
            if path.req_lock_space:  # 需要申请锁空间的旋转
                shelf_rotation_degrees = (
                    0
                    if self._is_need_sync_rotate_state_before_move()
                    else self.get_shelf_angle_offset_before_move()
                )
                space_type_req = self._get_space_type_from_lock_type(
                    REQ_SPACE_MOVE_ROTATE, shelf_rotation_degrees
                )
                if (
                    self._cur_execute_task
                    and not self._cur_execute_task.is_allow_to_rotate_with_shelf(
                        space_type_req, shelf_rotation_degrees
                    )
                ):
                    _logger.warning('cur task not allowed to rotate')
                    if self._cur_execute_task:
                        self._cur_execute_task.state = TaskState.SHELF_ANGLE_ERROR
                else:
                    self._request_lock_space(REQ_SPACE_MOVE_ROTATE, space_type_req)
                return
            else:
                # 旋转路径前可能需要开启同步旋转
                _logger.info('no need to lock space')
                if self._path_admin.is_rotate_path_group(self._move_paths):
                    result = self._sync_rotate_state_before_move()
                    if not result:
                        _logger.error('failed to open sync rotate before rotate path')
                        return
                else:
                    _logger.info(
                        'first path is rotate but path group has bezier,no need enable sync rotate'
                    )
        else:  # 移动
            is_need_rotate = self._need_rotate_shelf_before_move()
            if (
                is_need_rotate
                and path.type == PathType.PATH_LINE
                and GeometryUtils.calculate_distance(path.sx, path.sy, path.ex, path.ey)
                < SHORT_PATH_LEN_IN_50CM
                and (
                    len(self._move_paths) == 1
                    or (
                        len(self._move_paths) == 2
                        and self._move_paths[1].type == PathType.PATH_ROTATE
                    )
                )
            ):
                _logger.info('short line dont rotate shelf, if need rotate in destion')
                is_need_rotate = False
            _logger.info(
                f'path:{path} paths size:{len(self._move_paths)} is_need_rotate:{is_need_rotate}'
            )
            if (
                self._cur_execute_task
                and self._cur_execute_task.is_task_type_move_after_raise_shelf()
                and is_need_rotate
            ):
                shelf_rotation_degrees = self.get_shelf_angle_offset_before_move()
                space_type_req = self._get_space_type_from_lock_type(
                    REQ_SPACE_ROTATE_SHELF_BEFORE_MOVE, shelf_rotation_degrees
                )
                if self._cur_execute_task.is_allow_to_rotate_with_shelf(
                    space_type_req, shelf_rotation_degrees
                ):
                    self._request_lock_space(REQ_SPACE_ROTATE_SHELF_BEFORE_MOVE, space_type_req)
                else:
                    _logger.error('不允许旋转货架')
                    if self._cur_execute_task:
                        self._cur_execute_task.state = TaskState.SHELF_ANGLE_ERROR
                return

        # 不需要申请空间
        asyncio.run_coroutine_threadsafe(self._do_move_next_path(), self._loop)

    def _need_rotate_shelf_before_move(self) -> bool:
        """判断移动任务前，是否需要将货架转到目标角度"""
        if (
            self._config.is_device_riser_rotate()
            and self._srp_wrapper.is_system_idle()
            and self._srp_wrapper.is_load_full()
            and self._cur_execute_task.is_task_type_move_after_raise_shelf()
        ):
            # 举升货架叠加移动任务，移动前需要调整货架角度
            shelf_angle_to_robot = self._srp_wrapper.get_shelf_angle_to_robot()
            shelf_angle_in_global = self._srp_wrapper.get_shelf_angle_in_global()
            is_need_rotate = self._cur_execute_task.is_need_rotate_shelf_before_move(
                shelf_angle_to_robot
            )
            _logger.info(
                f'shelf to robot:{shelf_angle_to_robot:.1f}°, '
                f'shelf in global: {shelf_angle_in_global:.1f}°, '
                f'is_need_rotate_shelf: {is_need_rotate}'
            )
            return is_need_rotate
        return False

    def is_big_rotate_before_bezeir(self):
        """
        限制贝塞尔前的旋转角度，防止意外产生大角度带货架旋转:
        遇到贝塞尔前不申请锁空间的旋转，检查是否与小车当前角度偏差在10度内
        """
        if (
            len(self._move_paths) > 1
            and self._move_paths[0].type == PathType.PATH_ROTATE
            and not self._move_paths[0].req_lock_space
            and self._move_paths[1].type == PathType.PATH_BEZIER
        ):
            cur_angle = self._srp_wrapper.get_cur_angle()
            rotate_angle = math.degrees(self._move_paths[0].rotate_angle / 1000)
            delta = AngleUtils.delta_norm(cur_angle, rotate_angle)
            if delta > ALLOWED_ROTATE_ANGLE_BEFORE_BEZIER:
                _logger.error(f'贝塞尔前带货架旋转角度过大: {delta:.3f}°')
                return True
            elif delta > SHELF_ROTATE_ANGLE_THRESHOLD:
                _logger.warning(f'允许了贝塞尔前带货架旋转：{delta:.3f}°')

        return False

    async def _do_move_next_path(self):
        async with self._async_lock:
            if self._cur_execute_task is None:
                _logger.error('Move task is None')
                return

            _logger.info(self._path_admin)

            # 过滤贝塞尔前的大角度旋转
            if self.is_big_rotate_before_bezeir():
                self._cur_execute_task.state = TaskState.TASK_WRONG_ANGLE
                self.reset_task_state(False)
                return

            # 非旋转路径组，一次发送所有路径
            if (
                not self._path_admin.is_rotate_path_group(self._move_paths)
                and not self._need_rotate_shelf_before_move()
            ):
                # 圆弧路径时多条路径同时发送
                if self._do_move_path(self._move_paths):
                    if (
                        self._cur_execute_task.is_task_arc_move()
                        or self._cur_execute_task.is_task_type_with_multi_path_move()
                    ):
                        # 一般共三段路径,第一段为当前位置到圆弧起点直线路径,第二段为圆弧路径,第三段为圆弧终点到目标点直线路径,设置圆弧路径为当前路径
                        self._set_cur_move_path(
                            self._path_admin.get_latest_path_by_type(PathType.PATH_BEZIER)
                        )
                    else:
                        _logger.info('_set_cur_move_path by type')
                        path = self._path_admin.get_latest_path_by_type(PathType.PATH_LINE)
                        if path is None:
                            _logger.info('set cur path none, what happen')
                        self._set_cur_move_path(path)
                self._move_paths = []

                # 记录动作类型，供点检参考
                MiscUtils.append_unique(self._adapter._latest_actions, AutoCheckAction.AgvMove)
            # 旋转路径组，可能包含直线路径和旋转路径
            else:
                path = self._move_paths.pop(0)

                # 充电任务禁止旋转
                if path.type == PathType.PATH_ROTATE and self._cur_execute_task.is_start_charge():
                    _logger.error('No rotate in charge task')
                    self.reset_task_state()
                    return

                # 只有执行成功才更新，否则会出现报错后继续更新起始点，导致后续路径替换时由于起点不一样失败
                if self._do_move_path([path]):
                    self._set_cur_move_path(path)
                    if path.type != PathType.PATH_ROTATE:
                        _logger.info(f'Record path start points: {path.sx}, {path.sy}')

                # 记录动作类型，供点检参考
                MiscUtils.append_unique(self._adapter._latest_actions, AutoCheckAction.AgvRotate)

    def _do_move_path(self, paths):
        if not paths:
            _logger.warning('Error: Cannot send None path')
            return False

        # # 非替换路径方式下，系统状态非空闲，则忽略该路径，
        # # 解决由于存在时间差（系统状态上报时间延后，可能此时已经启动了任务），导致报ErrorCode.MOVEMENT_PRE_TASK_RUNNING
        # if self.is_replace_path() is False and self._srp_wrapper.is_system_idle() is False:
        #     _logger.warning("New movement task when system state is idle, ignore move")
        #     self._move_paths = []
        #     return False
        need_cancel_detect_dmcode = self._cur_execute_task.task_detail == TaskItem.Entry_Lift
        _logger.info(f'will send {len(paths)} path to robots:')
        for i, path in enumerate(paths):
            _logger.info(f'  {i}th: {path}')

        try:
            if self.is_replace_path():
                self._srp_wrapper.replace_move_path(paths, need_cancel_detect_dmcode)
            else:
                self._move_no = self._move_no + 1
                self._srp_wrapper.move_follow_path(self._move_no, paths, need_cancel_detect_dmcode)
                self.update_scurity_pose()
        except BaseException as e:
            # 执行失败后取消任务(如果报上一个任务还在执行，取消任务会导致任务结束后_cur_move_path=None)
            # self.reset_task_state()
            # 连续执行多条路径，会报错，但是不影响功能
            _logger.error(e, exc_info=True)
            result_code = self._srp_wrapper.get_result_code()
            if result_code == ErrorCode.PATH_REPLACE_MOVEMENT_TASK_NOT_RUNNING:
                # 由于不是替换路径，需要重新计算路径
                self._set_replace_path(False)
                asyncio.run_coroutine_threadsafe(
                    self._do_move_task(self._cur_execute_task), self._loop
                )
                return True
            elif result_code == ErrorCode.MOVEMENT_PRE_TASK_RUNNING:
                self._move_no = self._move_no - 1  # 如果不-1，会导致等待的no不匹配
                try:
                    # 由于存在时间差（系统状态上报时间延后，可能此时已经启动了任务），导致报ErrorCode.MOVEMENT_PRE_TASK_RUNNING
                    self._srp_wrapper.replace_move_path(paths, need_cancel_detect_dmcode)
                    return True
                except BaseException as e:
                    _logger.error(e, exc_info=True)
            # 出错后可以继续接收任务
            # 出错后复位会导致圆弧路径有问题，会失去替换路径的作用导致圆弧路径从头开始再执行一次
            if not self._cur_execute_task.is_task_arc_move():
                self.reset_task_state()
                self._reset_task_in_adapter()
            return False
        return True

    def _do_move_task_finish(self):
        _logger.info('move task finish')

        # 如果检测到异常，标记这个，跳过任务完成状态上报
        no_mark_task_done = False

        if self._cur_execute_task is None:
            _logger.warning('no cur task on task finish ?!')
            return

        # 充电任务，导航到充电桩后启动充电
        if self._cur_execute_task.is_charge_task():
            _logger.info('Current task is charge task')
            try:
                if self._cur_execute_task.is_start_charge():
                    charge_time = self._cur_execute_task.get_charge_time_in_second()
                    result = self.start_charge_for_seconds(charge_time)
                else:  # TODO 定时重启
                    result = True
                    pass

                # 没有执行充电或停止充电命令
                if not result:
                    _logger.error('Failed to start or stop charge')
                    self.reset_task_state()
                return
            except BaseException as e:
                _logger.error(e, exc_info=True)
        elif self._cur_execute_task.is_task_type_shelf_sn_detect():
            self._detect_shelf_sn = ''
            if self._do_execute_action(ActionID.DETECT_SVC, 1, self._cur_execute_task.detect_time):
                _logger.info('svc100 up scan Okay')
            else:
                _logger.error('svc100 up scan Failed')
                no_mark_task_done = True
        elif self._cur_execute_task.is_task_type_fork_action():
            if (
                self._cur_execute_task.is_task_type_fork_load_action()
                or self._cur_execute_task.is_task_type_fork_load_action_move_back()
            ):
                before_action_fork_height = self._cur_execute_task.actuator_info.raise_height
                after_action_fork_height = (
                    self._cur_execute_task.actuator_info.actuator_raise_height
                )
            else:
                before_action_fork_height = (
                    self._cur_execute_task.actuator_info.actuator_raise_height
                )
                after_action_fork_height = self._cur_execute_task.actuator_info.raise_height
            target_x = self._cur_execute_task.move_target.x
            target_y = self._cur_execute_task.move_target.y
            target_angle = self._cur_execute_task.move_target.angle
            if self._cur_execute_task.is_task_type_fork_load_action():
                load_dock_action_param = {}
                load_dock_action_param['action_id'] = 10162
                load_dock_action_param['target_x'] = target_x
                load_dock_action_param['target_y'] = target_y
                load_dock_action_param['target_fork_height'] = before_action_fork_height
                load_dock_action_param['after_action_target_fork_height'] = after_action_fork_height
                load_dock_action_param['target_angle'] = target_angle
                if not self._do_execute_action(10162, 0, 0, json.dumps(load_dock_action_param)):
                    _logger.info('load dock action failed, cant do 163')
                return

            elif self._cur_execute_task.is_task_type_fork_load_action_move_back():
                move_back_params = {}
                move_back_params['action_id'] = 10164
                move_back_params['target_x'] = target_x
                move_back_params['target_y'] = target_y
                move_back_params['target_angle'] = target_angle
                move_back_params['target_fork_height'] = before_action_fork_height
                if not self._do_execute_action(10164, 0, 0, json.dumps(move_back_params)):
                    _logger.info('move back after load failed, cant do 171')
                    return
                after_unload_lift_fork_action_param = {}
                after_unload_lift_fork_action_param['action_id'] = 10171
                after_unload_lift_fork_action_param['target_fork_height'] = after_action_fork_height
                after_unload_lift_fork_action_param['target_x'] = target_x
                after_unload_lift_fork_action_param['target_y'] = target_y
                after_unload_lift_fork_action_param['target_angle'] = target_angle
                if not self._do_execute_action(
                    10171, 0, 0, json.dumps(after_unload_lift_fork_action_param)
                ):
                    _logger.info('lift fork after unload failed')
                return

            elif self._cur_execute_task.is_task_type_fork_unload_action():
                unload_dock_action_param = {}
                unload_dock_action_param['action_id'] = 10172
                unload_dock_action_param['target_x'] = target_x
                unload_dock_action_param['target_y'] = target_y
                unload_dock_action_param['target_fork_height'] = before_action_fork_height
                unload_dock_action_param['after_action_target_fork_height'] = (
                    after_action_fork_height
                )
                unload_dock_action_param['target_angle'] = target_angle
                if not self._do_execute_action(10172, 0, 0, json.dumps(unload_dock_action_param)):
                    _logger.info('unload dock action failed, cannot do 173')
                return

            elif self._cur_execute_task.is_task_type_fork_unload_action_move_back():
                move_back_params = {}
                move_back_params['action_id'] = 10174
                move_back_params['target_x'] = target_x
                move_back_params['target_y'] = target_y
                move_back_params['target_angle'] = target_angle
                if not self._do_execute_action(10174, 0, 0, json.dumps(move_back_params)):
                    _logger.info('move back after unload failed')
                return

        elif self._cur_execute_task.is_task_type_arm_action():
            cur_pos = self._srp_wrapper.get_cur_pose()
            agv_angle = cur_pos['angle'] / 1000
            det_x = self._cur_execute_task.actuator_info.action_exten_pos_x - cur_pos['x']
            det_y = self._cur_execute_task.actuator_info.action_exten_pos_y - cur_pos['y']
            rack_in_agv_x = int(
                det_x * math.cos(math.radians(agv_angle))
                + det_y * math.sin(math.radians(agv_angle))
            )
            rack_in_agv_y = int(
                -det_x * math.sin(math.radians(agv_angle))
                + det_y * math.cos(math.radians(agv_angle))
            )
            paramStr = str(self._cur_execute_task.actuator_info.action_load_pos_type)
            paramStr += '|' + str(self._cur_execute_task.actuator_info.action_load_row_index)
            paramStr += '|' + str(self._cur_execute_task.actuator_info.action_load_arrange_index)
            paramStr += '|' + str(self._cur_execute_task.actuator_info.action_unload_pos_type)
            paramStr += '|' + str(self._cur_execute_task.actuator_info.action_unload_row_index)
            paramStr += '|' + str(self._cur_execute_task.actuator_info.action_unload_arrange_index)
            paramStr += '|' + str(rack_in_agv_x)
            paramStr += '|' + str(rack_in_agv_y)
            load_shelf_id = self._cur_execute_task.actuator_info.load_shelf_id
            unload_shelf_id = self._cur_execute_task.actuator_info.unload_shelf_id
            _logger.info(f'arm load rack id {load_shelf_id}')
            _logger.info(f'arm uload rack id {unload_shelf_id}')
            for i in range(0, 8):
                if i < len(load_shelf_id):
                    paramStr += '|' + str(ord(load_shelf_id[i]))
                else:
                    paramStr += '|' + '0'
            for i in range(0, 8):
                if i < len(unload_shelf_id):
                    paramStr += '|' + str(ord(unload_shelf_id[i]))
                else:
                    paramStr += '|' + '0'
            for _ in range(0, 20):
                self._retry_arm_task = True
                result = self._do_execute_action(
                    self._cur_execute_task.actuator_info.action_id,
                    self._cur_execute_task.actuator_info.action_param0,
                    self._cur_execute_task.actuator_info.action_param1,
                    paramStr,
                )
                if (
                    not result and self.get_raw_sros_task_result_code() == 340021
                ):  # 相应超时，eac那边可能阻塞
                    _logger.info('do eac action again')
                else:
                    _logger.info('do eac action success')
                    break
        elif (
            self._cur_execute_task.is_task_type_smt_move()
            and not self._cur_execute_task.is_execute_action_when_move
        ):
            self._do_smt_adjust_height_and_width(self._cur_execute_task)

        # 特定类型任务，移动结束，认为任务完成，准备上报完成状态
        if (
            not no_mark_task_done
            and self._cur_execute_task
            and (
                self._cur_execute_task.is_task_movement_mini()
                or self._cur_execute_task.is_task_type_shelf_sn_detect()
                or self._cur_execute_task.is_task_type_raise_shelf_only()
                or self._cur_execute_task.is_task_type_put_shelf_only()
            )
        ):
            _logger.info('mark task state as done')
            self._cur_execute_task.state = TaskState.DONE

        self.handle_post_mark_for_identity_shelf_leg()

        self._retry_arm_task = False
        self.reset_task_state(False)

    def _is_need_sync_rotate_state_before_move(self) -> bool:
        shelf_global_angle = self._srp_wrapper.get_shelf_angle_in_global()
        if not self._config.is_device_riser_rotate():
            return False

        if not self._srp_wrapper.is_load_full():
            return False

        if self._cur_execute_task is None:
            return False

        if self._cur_execute_task.is_no_sync_rotate_task():
            self._is_sync_rotate_on = False
            return False

        if not self._cur_execute_task.is_task_type_raise_shelf_only():  # 顶起货架回归必须开同步旋转
            if len(self._move_paths) == 1:
                _logger.info(f'start end rotate move, shelf_global_angle {shelf_global_angle:.2f}')
                # 如果货架角度没有相等，则不需要开启同步旋转(只有认为货架已经到位不需要旋转货架才开启同步旋转)
                # todo所有旋转都可以开启同步旋转，之后到达目标点在旋转货架到目标值,只是会浪费一些时间,此处逻辑不严格且多余
                if not self._cur_execute_task.is_equal_to_shelf_target_angle(
                    shelf_global_angle
                ) and self.is_equal_det_car_whith_det_shelf(self._cur_execute_task):
                    return False
        return True

    def _sync_rotate_state_before_move(self) -> bool:
        if not self._is_need_sync_rotate_state_before_move():
            return True

        if not self._do_sync_rotate_action(True):
            _logger.error('failed to open sync rotate before move')
            self._is_sync_rotate_on = False
            return False
        return True

    def is_equal_det_car_whith_det_shelf(self, task):
        cur_pose = self._srp_wrapper.get_cur_pose()
        det_car_angle = AngleUtils.normalize_360(
            task.move_target.angle / 1000
        ) - AngleUtils.normalize_360(cur_pose['angle'] / 1000)
        det_shelf_angle = AngleUtils.normalize_360(
            task.actuator_info.shelf_angle_at_dest / 1000
        ) - AngleUtils.normalize_360(self._srp_wrapper.get_shelf_angle_in_global())
        _logger.info(f'delta angle: car {det_car_angle:.2f}, shelf {det_shelf_angle:.2f}')
        return abs(det_car_angle - det_shelf_angle) < 3

    def _set_replace_path(self, is_replace):
        self._is_replace_path = is_replace

    def is_replace_path(self):
        return self._is_replace_path

    def _adjust_shelf_angle(self, is_action_4_2_0=False):
        """微调货架与小车的相对角度到就近的规则值: 0/90 度
        1. 只做小范围的角度旋转调整: <=SHELF_ROTATE_ANGLE_THRESHOLD
        2. 要求调整时小车当前角度应该贴近座标轴(偏差不超过5度)，否则不操作
        """

        # 由于状态上报存在延时，需主动请求同步状态
        self._srp_wrapper.sync_robot_state()
        cur_pose = self._srp_wrapper.get_cur_pose()
        angle = AngleUtils.normalize_360(cur_pose['angle'] / 1000)

        # 对于顶升后调整货架：此时小车与货架平行，如果货架不在 x/y 方向，偏差过大不调
        if AngleUtils.delta_90n(angle) > 5:
            _logger.info('is slam online path, no adjust shelf')
            return

        if not (self._config.is_device_riser_rotate() and self._srp_wrapper.is_load_full()):
            return

        # 货架与小车的角度偏差
        cur_angle = self._srp_wrapper.get_shelf_angle_to_robot()
        cur_angle_90_base = AngleUtils.to_90n(cur_angle)  # 二者偏差角度应该是 0/90, 最接近的规整角
        # 小车当前方向角度
        angle_robot = angle
        angle_robot_90_base = AngleUtils.to_90n(angle_robot)

        # 旋转角度的调整阀值
        adjust_threshold = SHELF_ANGLE_ADJUST_THRESHOLD
        if is_action_4_2_0:
            cur_angle_90_base += angle_robot_90_base - angle_robot
            adjust_threshold = 0.5

        # 相对角度就近调整到 0/90 度
        diff = AngleUtils.delta_norm(cur_angle_90_base, cur_angle)
        if diff > SHELF_ROTATE_ANGLE_THRESHOLD:
            _logger.warning(
                f'调整货架: delta_90n 偏差较大: {diff:.2f} > {SHELF_ROTATE_ANGLE_THRESHOLD} °'
            )
            return

        self._do_rotate_shelf(cur_angle, cur_angle_90_base, adjust_threshold)

    # 如果认为路网上规划的路径为A路径，包含A路径的任务称为A任务。非A路径是小车偏移拓扑路网情况下规划的，简称slam自主上线，小车只有在第一次上线以及启用货架退识别顶升货架后才会偏移路网
    # A路径是直线，A路径一定是水平或竖直的，非A路径可能是各种方向
    # A路径如果是曲线，起点水平或竖直,非A路径没有曲线
    # A任务如果有一条旋转A路径，那么不会在包含其他路径。非A任务可能包含旋转+直线+旋转
    # 以下情况旋转货架：
    # 1.在非旋转A路径之前，主要控制货架和小车相对角度
    # 2.执行完一条A旋转路径(也是整个任务结束)，旋转到任务目标角度
    # 3.A任务下微调货架相当小车角度，垂直或平行
    def _do_rotate_shelf(
        self, cur_angle, target_angle, threshold: float = SHELF_ROTATE_ANGLE_THRESHOLD
    ):
        _logger.info(f'do rotate shelf to robot,cur:{cur_angle:.1f}° target:{target_angle:.1f}°')
        if self._cur_execute_task is None or target_angle == ShelfAnglePolicy.Ignore:
            return False
        cur_pose = self._srp_wrapper.get_cur_pose()
        angle = AngleUtils.normalize_360(cur_pose['angle'] / 1000)
        if AngleUtils.delta_90n(angle) > 5:
            _logger.info('is slam online path, no rotate shelf')
            return True
        if AngleUtils.delta_norm(cur_angle, target_angle) > threshold:
            return self._do_execute_action(4, 12, round(target_angle * 10))  # 单位1/10度
        return True

    def _do_raise_shelf(self, allow_rotate=True):
        _logger.info('Do raise shelf')
        result = False
        if self._config.is_device_riser():
            result = self._do_execute_action(1, 1, 0)
        elif self._config.is_device_riser_rotate():
            if allow_rotate:
                result = self._do_execute_action(ActionID.SYNC_ROTATE, 1, 0)
            else:
                result = self._do_execute_action(ActionID.SYNC_ROTATE, 5, 0)
        else:
            _logger.error(f'device type not match on raise shelf: {self._config._car_type:#x}')
        return result

    def _do_put_shelf(self):
        _logger.info('Put down shelf')
        if self._config.is_device_riser():  # 顶升机构
            result = self._do_execute_action(1, 2, 0)
        elif self._config.is_device_riser_rotate():  # 旋转顶升
            # NOTE: 默认放货架自动回正顶板，除非任务判断不能转顶板
            if not self._cur_execute_task or self._cur_execute_task.is_allow_to_rotate_plate(
                load_full=False
            ):
                result = self._do_execute_action(ActionID.SYNC_ROTATE, 2, 0)
            else:
                result = self._do_execute_action(ActionID.SYNC_ROTATE, 11, 0)
                if result:
                    shelf_angle_to_robot = self._srp_wrapper.get_shelf_angle_to_robot()
                    shelf_angle_fit_90n = AngleUtils.to_90n(shelf_angle_to_robot)
                    delta_angle = AngleUtils.delta_norm(shelf_angle_to_robot, shelf_angle_fit_90n)
                    if delta_angle > SHELF_ROTATE_ANGLE_THRESHOLD:
                        _logger.warning(
                            f'放货架后顶板角度偏离 90n 过大，货架相对小车 {shelf_angle_to_robot:.3f}°'
                        )
                    else:
                        # 单位1/10度
                        self._do_execute_action(4, 12, round(shelf_angle_fit_90n * 10))

        else:
            _logger.error(f'car type not match on put shelf: {self._config._car_type:#x}')
            result = False
        return result

    def _do_check_and_recover_shelf_angle_after_sync_rotate(self, restrict_move=False):
        """同步旋转关闭时检查调整货架角度

        目标：在同步旋转结束后，
        1. 小车方向 90n, 原来货架角度靠近 90n, 货架最好直接回到 90n
        2. 小车方向 90n, 原来货架角度不在 90n, 货架还是回原来角度
            # 例外：货架角度同步旋转后回到了 90n (可能是开了同步旋转二次矫正)
        3. 小车不在 90n 方向，原来货架什么角度，就应该还是什么角度

        安全限制：
        1. 最终调整角度小于某个阀值
        2. 前后小车位置的直线距离应该在较小距离内（如果限制移动）
        3. 如果中间有任务状态重置，不再执行检查调整
        """
        # 调整策略允许转顶板才行
        if not self._cur_execute_task or not self._cur_execute_task.is_allow_to_rotate_plate(
            load_full=self._srp_wrapper.is_load_full()
        ):
            return

        # 检查矫正同步旋转偏差
        if self._shelf_angle_before_sync_rotate is None:
            return

        # 检查同步旋转期间位置移动
        if restrict_move and self._robot_pose_before_sync_rotate:
            old_pose = self._robot_pose_before_sync_rotate
            cur_pose = self._srp_wrapper.get_cur_pose()
            move_distance = GeometryUtils.calculate_distance(
                old_pose['x'], old_pose['y'], cur_pose['x'], cur_pose['y']
            )

            if move_distance > MAX_MOVE_DISTANCE_FOR_SYNC_ROTATE:
                _logger.warning(f'跳过矫正，同步旋转前后距离偏差过大：{move_distance:.2f}mm')
                self._shelf_angle_before_sync_rotate = None
                self._robot_pose_before_sync_rotate = None
                return

        shelf_angle_target = self._shelf_angle_before_sync_rotate
        shelf_angle_after_sync_rotate = self._srp_wrapper.get_shelf_angle_in_global()
        robot_angle = self._srp_wrapper.get_cur_angle()

        # 货架一步到位:
        #   1. 小车当前和货架同步旋转前都在 90n 方向
        #   2. 货架当前已经在 90n 方向  (可能开了同步旋转自动矫正回去了)
        if (
            AngleUtils.delta_90n(robot_angle) < SHELF_ROTATE_ANGLE_THRESHOLD
            and AngleUtils.delta_90n(shelf_angle_target) < SHELF_ROTATE_ANGLE_THRESHOLD
        ) or AngleUtils.delta_90n(shelf_angle_after_sync_rotate) < SHELF_ROTATE_ANGLE_THRESHOLD:
            shelf_angle_target = AngleUtils.to_90n(shelf_angle_target)

        # 要转到目标位置需要转多大角度
        shelf_angle_delta = AngleUtils.delta_norm(shelf_angle_after_sync_rotate, shelf_angle_target)

        _logger.info(
            '同步旋转前后顶板角度及矫正目标角度(deg):'
            f'{self._shelf_angle_before_sync_rotate:.2f}->{shelf_angle_after_sync_rotate:.2f},'
            f'target: {shelf_angle_target:.2f}, delta: {shelf_angle_delta:.2f}'
        )

        # 412 角度参数是相对角度：相对小车逆时针旋转的角度(有方向)
        target_angle_for_412 = (shelf_angle_target - robot_angle) % 360

        # 检查矫正
        if shelf_angle_delta > MAX_SHELF_ANGLE_TO_RECOVER_FOR_SYNC_ROTATE:
            _logger.warning('矫正目标需要旋转角度过大，放弃矫正')
        elif shelf_angle_delta > MIN_SHELF_ANGLE_TO_RECOVER_FOR_SYNC_ROTATE:
            self._do_execute_action(4, 12, round(target_angle_for_412 * 10))  # 单位1/10度

        self._robot_pose_before_sync_rotate = None
        self._shelf_angle_before_sync_rotate = None

    def _do_sync_rotate_action(self, is_on):
        self._is_sync_rotate_on = is_on
        if is_on:
            self._shelf_angle_before_sync_rotate = None
            self._robot_pose_before_sync_rotate = None
            ret = self._do_execute_action(ActionID.SYNC_ROTATE, 13, 0)
            if (
                ret
                and self._cur_execute_task
                and self._cur_execute_task.is_allow_to_rotate_plate(
                    load_full=self._srp_wrapper.is_load_full()
                )
            ):  # 记录同步旋转前货架角度，小车位置
                self._shelf_angle_before_sync_rotate = self._srp_wrapper.get_shelf_angle_in_global()
                self._robot_pose_before_sync_rotate = self._srp_wrapper.get_cur_pose()
            return ret
        else:
            ret = self._do_execute_action(ActionID.SYNC_ROTATE, 14, 0)
            if ret:
                self._do_check_and_recover_shelf_angle_after_sync_rotate(restrict_move=True)
            return ret

    def _do_dmcode_adjust(self):
        return self._do_execute_action(7, 2, 0)

    def _do_roller_action(self, idx, action_type, direction):
        result = False
        for _ in range(0, 80):
            _logger.info(f'_do_roller_action: {idx} {action_type} {direction}')
            valid_roller_num = self._cur_execute_task.get_valid_roller_dat_number()
            if self._config.is_device_single_roller() and valid_roller_num == 1:  # 单层辊筒
                if action_type == ROLLER_ACTION_FETCH:
                    result = self._do_execute_action(192, 1, 11)
                elif action_type == ROLLER_ACTION_PUT:
                    result = self._do_execute_action(192, 1, 12)
                elif action_type == ROLLER_ACTION_STOP:
                    result = self._srp_wrapper.cancel_task()
            elif self._config.is_device_dlayer_roller():  # 双层辊筒
                if idx % 2 == 0:  # 上面辊筒
                    if action_type == ROLLER_ACTION_FETCH:
                        result = self._do_execute_action(192, 2, 1)
                    # elif action_type == ROLLER_ACTION_PUT:
                    #     result = self._do_execute_action(192, 1, 2)
                    elif action_type == ROLLER_ACTION_STOP:
                        result = self._srp_wrapper.cancel_task()
                else:  # 下面辊筒
                    if action_type == ROLLER_ACTION_FETCH:
                        result = self._do_execute_action(192, 1, 1)
                    elif action_type == ROLLER_ACTION_PUT:
                        result = self._do_execute_action(192, 1, 2)
                    elif action_type == ROLLER_ACTION_STOP:
                        result = self._srp_wrapper.cancel_task()
            # elif self._config.is_device_drow_layer():  # 双排辊筒
            #     if idx != 0 and idx != 1:
            #         return result
            #     if action_type == ROLLER_ACTION_FETCH:
            #         if direction == ROLLER_DIR_LEFT_OR_FORWARD:
            #             result = self._do_execute_action(3, 3, idx)
            #         else:
            #             result = self._do_execute_action(3, 1, idx)
            #     elif action_type == ROLLER_ACTION_PUT:
            #         if direction == ROLLER_DIR_LEFT_OR_FORWARD:
            #             result = self._do_execute_action(3, 4, idx)
            #         else:
            #             result = self._do_execute_action(3, 2, idx)
            #     elif action_type == ROLLER_ACTION_STOP:
            #         result = self._srp_wrapper.cancel_task()
            if not result and (self.get_raw_sros_task_result_code() in (1702, 1710)):
                _logger.info('will do roller again')
                continue
            break
        return result

    def _do_execute_action(self, action_id, param0, param1, paramStr=''):
        try:
            self._action_no += 1
            _logger.info(
                f'[[[[[ action task: {self._action_no}({action_id}, {param0}, {param1}, {paramStr})'
            )
            action_task = self._srp_wrapper.execute_action_task(
                self._action_no, action_id, param0, param1, paramStr
            )
            assert action_task is not None
            self._task_result = action_task.result
            self._task_result_code = action_task.result_code
            self._task_result_str = action_task.result_str
            action_id = action_task.id
            param0 = action_task.param0
            param1 = action_task.param1
            _logger.info(
                f']]]]] action task {action_task.no}({action_id}, {param0}, {param1}) finished! '
                f'result: ({self._task_result}, {self._task_result_code}, {self._task_result_str})'
            )

            # 记录动作，供点检上报
            if action_id == 4:
                if param0 in (1, 5, 11):
                    MiscUtils.append_unique(
                        self._adapter._latest_actions, AutoCheckAction.LiftUpDown
                    )
                elif param0 == 12:
                    MiscUtils.append_unique(
                        self._adapter._latest_actions, AutoCheckAction.LiftRotate
                    )

            if action_id == ActionID.DETECT_SVC and param0 == 1:
                shelf_sn, _, _, yaw = self._srp_wrapper.parse_dmcode_info(self._task_result_str)
                if shelf_sn and shelf_sn != '-':
                    self._last_shelf_sn = shelf_sn
                self._detect_shelf_sn = shelf_sn
                self._detect_shelf_angle = AngleUtils.normalize_360(
                    self._srp_wrapper.get_cur_angle() - yaw
                )
            if action_task.result == main_pb2.TASK_RESULT_OK:
                _logger.info('Action task execute Okay')
                return True
                # 动作执行完成，不设置_cur_execute_task=None
                # 以免影响动作机构状态上传
            elif action_task.result == main_pb2.TASK_RESULT_CANCELED:
                _logger.info('Action task is cancelled')
                self.reset_task_state(False)
                return False
            elif action_task.result == main_pb2.TASK_RESULT_FAILED:
                _logger.info('Action task failed')
                self.reset_task_state(False)
                return False
            return False
        except BaseException as e:
            _logger.error(f'Execute action task failed: {e}', exc_info=True)
            self.reset_task_state()
            return False

    def start_charge_for_seconds(self, interval):
        _logger.info(f'Start charge for {interval / 60} min')
        battery_info = self._srp_wrapper.get_battery_info()
        if battery_info['percent'] > 98:
            return False
        if battery_info['status'] == main_pb2.HardwareState.BatteryState.BATTERY_NO_CHARGING:
            try:
                self._srp_wrapper.start_charge(self._seq)
                # self._srp_wrapper.start_charge()
                self._seq += 1
                self.send_charge_cmd_before_send_stop = True
                self.resend_charge_cmd_time = 0
            except BaseException as e:
                _logger.error(e, exc_info=True)
                return False
        self._start_charge_timer(interval)
        return True

    def resend_charge_cmd_if_error(self):
        if self.send_charge_cmd_before_send_stop and not self._srp_wrapper.is_charging():
            _logger.info('send charge cmd again')
            self._srp_wrapper.start_charge(self._seq)
            self.resend_charge_cmd_time += 1
            self._seq += 1

    def stop_charge_if_full(self):
        if not self.send_charge_cmd_before_send_stop:
            return
        battery_info = self._srp_wrapper.get_battery_info()
        if battery_info['percent'] > 98:
            self.stop_charge()

    def stop_charge(self):
        _logger.info('Stop charge')
        # 停止充电时，复位任务状态，以准备接收下一个任务
        self.reset_task_state()
        self._stop_charge_timer()
        battery_info = self._srp_wrapper.get_battery_info()
        if battery_info['status'] == main_pb2.HardwareState.BatteryState.BATTERY_CHARGING:
            try:
                self._srp_wrapper.stop_charge(self._seq)
                self._seq += 1
                self.send_charge_cmd_before_send_stop = False
                self.resend_charge_cmd_time = 0
                return True
            except BaseException as e:
                _logger.error(e, exc_info=True)
        return False

    def _start_charge_timer(self, interval):
        self._stop_charge_timer()
        self._charge_timer = Timer(interval, self.stop_charge)
        self._charge_timer.start()

    def _stop_charge_timer(self):
        if self._charge_timer:
            self._charge_timer.cancel()
        self._charge_timer = None

    def _get_cur_move_path(self):
        return self._cur_move_path

    def _set_cur_move_path(self, path):
        self._cur_move_path = path

    async def _calculate_move_path(self, task):
        async with self._async_lock:
            paths = []
            cur_pos = self._srp_wrapper.get_cur_pose()
            if self.is_replace_path():
                # 获取替换路径的起始点
                # is_append: 替换路径时是否以追加方式替换
                # 1、直线路径替换直线路径，圆弧路径替换圆弧路径且弧线点相同，此时应该将原来路径组替换，
                # 使用原路径组的第一条路径起点作为替换路径起点
                # 2 如果直线路径->圆弧路径和圆弧路径->直线路径方式的替换，
                #   最后一段路径的坐标和方向作为替换路径起点, 新路径组以追加方式替换原路径组
                # 替换路径需要考虑初始角度，否则圆弧路径替换时会导致使用当前小车角度算出奇怪的旋转路径
                is_append = True
                if self._cur_execute_task and (
                    (task.is_task_linear_move() and self._cur_execute_task.is_task_linear_move())
                    or (
                        self._cur_execute_task.is_task_arc_move()
                        and task.is_task_arc_move()
                        and self._cur_execute_task.is_same_arc_points(task.path_points)
                    )
                ):
                    is_append = False

                replace_pose = self._path_admin.get_replace_path_start_pose(is_append)

                # 处理多路径出弧线后目标点及速度替换(最后的直线路径替换)，
                # 新任务没有起点信息，使用最后的直线作为起点，限速立即更新
                if task.is_task_linear_move() and self.may_replace_last_line(
                    task.move_target.x, task.move_target.y
                ):
                    last_path = self._path_admin.get_last_path()
                    assert last_path

                    # 需要检查移动方向不变：原路径起点 A，当前目标点 B，当前点 C: (AB,CB) 方向相同
                    # 因为新任务没有起点信息，使用前一条路径的起点(这样会在后面发送路径前过滤替换)

                    new_path = Path.create_line_path(
                        cur_pos['x'], cur_pos['y'], task.move_target.x, task.move_target.y
                    )

                    # 到终点距离大于 20cm 才考虑替换
                    if new_path.length >= 200:
                        last_angle = last_path.begin_facing()
                        cur_angle = new_path.begin_facing()

                        # 实际位置不一定在直线上，这里 20cm 只要直线方向角度不超过 60 度，就沿用前面起点
                        if AngleUtils.delta_norm(last_angle, cur_angle, absolute=True) < 60:
                            is_append = False
                            replace_pose = {
                                'x': last_path.sx,
                                'y': last_path.sy,
                                'angle': int(last_angle * 1000),
                            }
                        else:
                            _logger.warning(
                                f'小车当前位置到目标方向与路径角度偏差过大: {last_angle} vs {cur_angle} deg'
                            )

                _logger.info(f'Replace path start pose: append={is_append} {replace_pose}')
                if replace_pose is None:
                    _logger.error('Replace pose is None')
                    replace_pose = cur_pos
                    self._set_replace_path(False)
                cur_pos = replace_pose

            try:
                if task is None:
                    _logger.error('_calculate_move_path: Current task is none')
                    return paths

                # 计算路径前重置偏航状态
                if task.state == TaskState.NAV_OFF_PATH:
                    task.state = TaskState.NONE

                self._path_admin.set_path_start_pose(cur_pos)
                paths = task.calculate_move_path(
                    cur_pos, any_move=self._config.is_device_all_direction()
                )

                # 更新切线
                # if len(paths) > 0:
                #     self._update_tangent_slope()
            except BaseException as e:
                _logger.error(e, exc_info=True)
            _logger.info(f'device move total path number: {len(paths)}')
            for i, path in enumerate(paths):
                _logger.info(f'  {i}th: {path}')
            return paths

    def _update_tangent_slope(self, task):
        if task is None:
            return
        target_angle = task.get_target_angle()
        target_angle = AngleUtils.normalize_180(target_angle / 1000)
        if AngleUtils.equal_norm(target_angle, ANGLE_90, 1) or AngleUtils.equal_norm(
            target_angle, ANGLE_MINUS_90, 1
        ):
            # 斜率无穷大
            self._path_tangent_slope = float('inf')
        else:
            self._path_tangent_slope = math.tan(math.radians(target_angle))
        _logger.info(f'update path slope {self._path_tangent_slope}')
