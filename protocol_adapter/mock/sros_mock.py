#!/usr/bin/python3

import time
import queue
import math
import logging

from enum import Enum
from typing import Optional, Tuple
from threading import Thread

from protocol_adapter.mock.smt_actuator_mock import SmtActuatorMock
from protocol_adapter.protobuf_wrapper import main_pb2, monitor_pb2
from protocol_adapter.protobuf_wrapper.base import Point, Pose, rotate_to_target
from protocol_adapter.protobuf_wrapper.path import Path, PathType, Direction
from protocol_adapter.mock.world_mock import WorldMock
from protocol_adapter.mock.lift_rotate_actuator_mock import LiftRotateActuatorMock
from protocol_adapter.mock.roller_actuator_mock import RollerActuatorMock
from protocol_adapter.const import ActuatorType
from protocol_adapter.utils import AngleUtils

_logger = logging.getLogger(__name__)
# 若没特殊说明，单位统一用角度和米,角度[0, 360)

LOOP_INTERVAL = 0.2  # seconds
ROTATE_SPEED = 30  # per seconds
ROTATE_STEP = ROTATE_SPEED * LOOP_INTERVAL
ANGLE_ACCEPT_DIFF = 0.1  # 可接受的角度偏差
MOVE_SPEED = 1  # m/s
MOVE_STEP = MOVE_SPEED * LOOP_INTERVAL


def move_to_target_at_line(path: Path, src: Point, step: float) -> Point:
    """从src跟随path移动,每次最多移动step。返回这一次移动到的位置"""
    assert path.type == PathType.PATH_LINE, f'只支持直线, path.type:{path.type}'
    dst = Point(path.ex, path.ey)
    if math.dist(src, dst) < step:
        return dst
    rad = math.atan2(dst.y - src.y, dst.x - src.x)
    return Point(math.cos(rad), math.sin(rad)) * step + src


def get_pose_from_bezier(path: Path, t: float) -> Pose:
    t = max(0.0, min(1.0, t))
    ax = (path.cx - path.sx) * t + path.sx
    ay = (path.cy - path.sy) * t + path.sy
    bx = (path.dx - path.cx) * t + path.cx
    by = (path.dy - path.cy) * t + path.cy
    cx = (path.ex - path.dx) * t + path.dx
    cy = (path.ey - path.dy) * t + path.dy
    dx = (bx - ax) * t + ax
    dy = (by - ay) * t + ay
    ex = (cx - bx) * t + bx
    ey = (cy - by) * t + by
    px = (ex - dx) * t + dx
    py = (ey - dy) * t + dy
    yaw = math.atan2(ey - dy, ex - dx)
    degree = path.get_face_angle_with_respect_to_direction(math.degrees(yaw))
    return Pose(px, py, AngleUtils.normalize_360(degree))


def move_to_target_at_bezier(path: Path, t: float, step: float) -> Tuple[Pose, float]:
    """跟随path移动,每次最多移动step, t为上次迭代。返回这一次移动到的位置,和此次t"""
    assert path.type == PathType.PATH_BEZIER, f'只支持贝塞尔, path.type:{path.type}'
    t = max(0.0, min(1.0, t))
    if t >= 1.0:
        return get_pose_from_bezier(path, 1.0), 1.0
    # 此处为了简化计算，step不是很准
    det_pos = step / 2  # 为了简化直接用主线距离来判断step
    cur_pose = get_pose_from_bezier(path, t)
    det_t: float = 1.0 / 1000.0
    while True:
        t += det_t
        t = max(0, min(1, t))
        pose = get_pose_from_bezier(path, t)
        if t >= 1:
            return pose, 1
        if math.dist(cur_pose.point(), pose.point()) >= det_pos:
            return pose, t


class SrosMock:
    def __init__(self, actuator_type=ActuatorType.Lift_Rotate):
        self.system_state = main_pb2.SystemState()
        self.hardware_state = main_pb2.HardwareState()
        self.sensor_samples = monitor_pb2.SensorDataCollection()
        self._movement_task = main_pb2.MovementTask()
        self._tmp_config = {}
        # 系统状态
        self._req_seq = 0
        self._sys_state = main_pb2.SystemState.SYS_STATE_IDLE
        self._location_state = main_pb2.SystemState.LOCATION_STATE_RUNNING
        self._operation_state = main_pb2.SystemState.OPERATION_AUTO
        self._map_name = 'AA'
        # 硬件状态
        self._break_sw_state = main_pb2.HardwareState.BREAK_SW_OFF
        self._battery_state = main_pb2.HardwareState.BATTERY_NO_CHARGING
        self.battery_nominal_capacity = 22430  # mAh
        self.battery_remain_capacity = self.battery_nominal_capacity * 0.94  # mAh
        # 运动控制有关
        self._curr_pose = Pose()
        self._curr_bezier_t: float = 0.0
        self._cur_v = 0  # 当前速度
        # 动作相关变量
        self.actuator_type = actuator_type
        self._action_task = main_pb2.ActionTask()
        if self.actuator_type == ActuatorType.Lift_Rotate:
            self._actuator = LiftRotateActuatorMock(LOOP_INTERVAL)
        elif self.actuator_type == ActuatorType.Roller:
            self._actuator = RollerActuatorMock(LOOP_INTERVAL)
        elif self.actuator_type == ActuatorType.Smt:
            self._actuator = SmtActuatorMock(LOOP_INTERVAL)
        else:
            raise ValueError(f'当前不支持此执行结构类型，{self.actuator_type}')

        self._cmd_queue = queue.SimpleQueue()

        self._is_running = False

        self._callback_system_state = None
        self._callback_connect_changed = None
        self._callback_move_task_finish = None
        self._callback_hardware_state = None
        self._callback_laser_point = None
        self._callback_sensor_samples = None

    def set_callback_connect(self, fun):
        self._callback_connect_changed = fun

    def set_system_state_callback(self, fun):
        self._callback_system_state = fun

    def set_hardware_state_callback(self, fun):
        self._callback_hardware_state = fun

    def set_sensor_samples_callback(self, fun):
        self._callback_sensor_samples = fun

    def set_laser_point_callback(self, fun):
        self._callback_laser_point = fun

    def set_notify_move_task_finished_callback(self, fun):
        self._callback_move_task_finish = fun

    def set_notify_action_task_finished_callback(self, fun):
        self._actuator.set_notify_action_task_finished_callback(fun)

    def run(self):
        t = Thread(target=self._loop, name='SrosMock')
        t.start()

    def stop(self):
        self._is_running = False

    def set_pose(
        self,
        pose: Pose,
        shelf_pose: Optional[Pose] = None,
        shelf_id: str = '',
        map_name: str = '',
    ):
        """测试专用，设置最开始车的位置, shelf_pose不为None时，表示最开始车就背起了货架"""
        _logger.debug(
            f'set_pose {pose}, shelf_pose：{shelf_pose}, shelf_id：{shelf_id}, map: {map_name}'
        )
        self._curr_pose = pose
        self._curr_pose.yaw = AngleUtils.normalize_360(self._curr_pose.yaw)

        if shelf_pose:
            assert pose.distance(shelf_pose) < 1, (
                f'背起货架时，货架的位置和车的位置，相差无几。shelf_pose：{shelf_pose}'
            )
            assert shelf_id, '需要设置货架ID'
            shelf_pose.yaw = AngleUtils.normalize_360(shelf_pose.yaw)
            self._actuator.load_state = main_pb2.SystemState.LOAD_FULL
            self._actuator.rotate_value = AngleUtils.normalize_360(
                shelf_pose.yaw - self._curr_pose.yaw
            )
            self._actuator.shelf_id = shelf_id
            world = WorldMock()
            world.set_shelf(shelf_id, shelf_pose)

        if map_name:
            self._map_name = map_name

    def set_hw_state(self, **kwargs):
        _logger.debug(f'set_hw_state: {kwargs}')

        battery_percentage = kwargs.get('battery_percentage', 1)
        if 0 < battery_percentage <= 1:
            self.battery_remain_capacity = self.battery_nominal_capacity * battery_percentage

    def map_switching(self, map_name: str, x, y, angle, absolute_location: bool) -> bool:
        """切换地图"""
        pose = Pose(x, y, angle)
        self._cmd_queue.put(
            {
                'type': main_pb2.CMD_MAP_SWITCHING,
                'map_name': map_name,
                'pose': pose,
                'absolute_location': absolute_location,
            }
        )
        while True:
            if (
                self._location_state == main_pb2.SystemState.LOCATION_STATE_RUNNING
                and self._map_name == map_name
            ):
                break
            time.sleep(0.1)
        return True

    def move_follow_path(self, no, paths, cancel_task_decetect_dmcode=False):
        self.assert_new_path_start_path_is_valid(paths)
        self.assert_new_paths_is_valid(paths)
        movement_task = main_pb2.MovementTask(
            no=no,
            type=main_pb2.MovementTask.MT_MOVE_FOLLOW_PATH,
            avoid_policy=main_pb2.MovementTask.OBSTACLE_AVOID_WAIT,
        )
        for path in paths:
            proto_path = movement_task.paths.add()
            proto_path.type = path.type
            proto_path.sx = path.sx
            proto_path.sy = path.sy
            proto_path.ex = path.ex
            proto_path.ey = path.ey
            proto_path.cx = path.cx
            proto_path.cy = path.cy
            proto_path.dx = path.dx
            proto_path.dy = path.dy
            proto_path.radius = path.radius
            proto_path.rotate_angle = path.rotate_angle
            if isinstance(path.direction, Enum):
                proto_path.direction = path.direction
            else:
                proto_path.direction = path.direction
            proto_path.limit_v = path.limit_v
            proto_path.limit_w = path.limit_w
        self._cmd_queue.put(
            {'type': main_pb2.CMD_NEW_MOVEMENT_TASK, 'movement_task': movement_task}
        )

    def execute_action_task(self, no, action_id, param0, param1, param_str=''):
        action_task = main_pb2.ActionTask(
            no=no, id=action_id, param0=param0, param1=param1, param_str=param_str
        )
        self._cmd_queue.put({'type': main_pb2.CMD_NEW_ACTION_TASK, 'action_task': action_task})

    def sync_execute_action_task(self, no, action_id, param0, param1, param_str=''):
        """同步执行动作任务，直到任务完成"""
        self.execute_action_task(no, action_id, param0, param1, param_str)
        while True:
            if (
                self._action_task.no == no
                and self._action_task.state == main_pb2.ActionTask.AT_FINISHED
            ):
                break
            time.sleep(0.1)
        return self._action_task

    def set_sros_cache_configs(self, configs):
        _logger.info(f'Set SrosCacheConfigs: {configs}')
        self._tmp_config = configs

    def start_charge(self) -> None:
        world = WorldMock()
        if world.is_get_charging_station(self._curr_pose):
            self._battery_state = main_pb2.HardwareState.BATTERY_CHARGING
            _logger.info('启动充电成功')
        else:
            _logger.error(
                f'当前车辆不在充电桩附近，无法进行充电！{self._curr_pose}, {world.get_charging_station_pose()}'
            )

    def stop_charge(self) -> None:
        if self._battery_state == main_pb2.HardwareState.BATTERY_CHARGING:
            self._battery_state = main_pb2.HardwareState.BATTERY_NO_CHARGING
            _logger.info('停止充电成功')
        else:
            _logger.error('当前不在充电状态，无法停止充电')

    def pause_task(self):
        self._cmd_queue.put({'type': main_pb2.CMD_PAUSE_MOVEMENT})

    def continue_task(self):
        self._cmd_queue.put({'type': main_pb2.CMD_CONTINUE_MOVEMENT})

    def cancel_task(self):
        self._cmd_queue.put({'type': main_pb2.CMD_COMMON_CANCEL})

    def cancel_movement_task(self, soft_cancel):
        self._cmd_queue.put({'type': main_pb2.CMD_CANCEL_MOVEMENT_TASK, 'paramBool': soft_cancel})

    def enable_manual_control(self):
        self._cmd_queue.put({'type': main_pb2.CMD_ENABLE_MANUAL_CONTROL})

    def disable_manual_control(self):
        self._cmd_queue.put({'type': main_pb2.CMD_DISABLE_MANUAL_CONTROL})

    def enable_traffic_control(self):
        # TODO: zz: traffic control
        pass

    def disable_traffic_control(self):
        # TODO: zz: traffic control
        pass

    def replace_move_path(self, paths):
        self.assert_new_paths_is_valid(paths)
        proto_paths = []
        for path in paths:
            proto_path = main_pb2.Path()
            proto_path.type = path.type
            proto_path.sx = path.sx
            proto_path.sy = path.sy
            proto_path.ex = path.ex
            proto_path.ey = path.ey
            proto_path.cx = path.cx
            proto_path.cy = path.cy
            proto_path.dx = path.dx
            proto_path.dy = path.dy
            proto_path.radius = path.radius
            proto_path.rotate_angle = path.rotate_angle
            if isinstance(path.direction, Enum):
                proto_path.direction = path.direction
            else:
                proto_path.direction = path.direction
            proto_path.limit_v = path.limit_v
            proto_path.limit_w = path.limit_w
            proto_paths.append(proto_path)
        self._cmd_queue.put({'type': main_pb2.CMD_PATH_REPLACE, 'paths': proto_paths})

    def _loop(self):
        self._is_running = True
        while self._is_running:
            time.sleep(LOOP_INTERVAL)
            try:
                self._handle_cmd()
                self._handle_running_movement_task()
                self._handle_running_action_task()
                self._update_system_state()
                self._update_hardware_state()
            except Exception as e:
                _logger.debug(f'loop e: {e}', exc_info=True)

    def _handle_cmd(self):
        while True:
            try:
                cmd = self._cmd_queue.get_nowait()
                if cmd['type'] == main_pb2.CMD_MAP_SWITCHING:
                    self._handle_map_switching(
                        cmd['map_name'], cmd['pose'], cmd['absolute_location']
                    )
                elif cmd['type'] == main_pb2.CMD_ENABLE_MANUAL_CONTROL:
                    self._operation_state = main_pb2.SystemState.OPERATION_MANUAL
                elif cmd['type'] == main_pb2.CMD_DISABLE_MANUAL_CONTROL:
                    self._operation_state = main_pb2.SystemState.OPERATION_AUTO
                elif cmd['type'] == main_pb2.CMD_NEW_MOVEMENT_TASK:
                    self._handle_new_movement_task(cmd['movement_task'])
                elif cmd['type'] == main_pb2.CMD_NEW_ACTION_TASK:
                    self._handle_new_action_task(cmd['action_task'])
                elif cmd['type'] == main_pb2.CMD_PAUSE_MOVEMENT:
                    self._handle_pause_task()
                elif cmd['type'] == main_pb2.CMD_CONTINUE_MOVEMENT:
                    self._handle_continue_task()
                elif cmd['type'] == main_pb2.CMD_COMMON_CANCEL:
                    self._handle_cancel_task()
                elif cmd['type'] == main_pb2.CMD_CANCEL_MOVEMENT_TASK:
                    self._handle_cancel_movement_task(cmd['paramBool'])
                elif cmd['type'] == main_pb2.CMD_PATH_REPLACE:
                    self._handle_replace_move_path(cmd['paths'])
                else:
                    assert False, f'未知命令：{cmd}'
            except queue.Empty:
                break

    def _handle_map_switching(self, map_name: str, pose: Pose, absolute_location: bool):
        _logger.debug(f'CMD_MAP_SWITCHING {map_name} {pose} {absolute_location}')
        self._map_name = map_name
        self._curr_pose = pose
        self._location_state = main_pb2.SystemState.LOCATION_STATE_RUNNING

    def _handle_new_movement_task(self, task):
        _logger.debug(f'CMD_NEW_MOVEMENT_TASK {task}')
        if task.no == self._movement_task.no:
            _logger.error(f'重复启动任务：{task}')
            return
        if self._movement_task.state not in [
            main_pb2.MovementTask.MT_FINISHED,
            main_pb2.MovementTask.MT_NA,
        ]:
            _logger.error(f'当前有任务执行：{self._movement_task}')
            return
        task.state = main_pb2.MovementTask.MT_WAIT_FOR_START
        self._sys_state = main_pb2.SystemState.SYS_STATE_TASK_NAV_INITIALING
        self._movement_task = task

    def _handle_new_action_task(self, task: main_pb2.ActionTask) -> None:
        _logger.info(f'CMD_NEW_ACTION_TASK {task}')
        if task.no == self._action_task.no:
            _logger.error(f'重复启动任务：{task}')
            return
        if self._action_task.state not in [
            main_pb2.ActionTask.AT_FINISHED,
            main_pb2.ActionTask.AT_ZERO,
        ]:
            _logger.error(f'当前有任务执行：{self._action_task}')
            return
        task.state = main_pb2.ActionTask.AT_WAIT_FOR_START
        self._action_task = task
        self._actuator.set_action(self._action_task)

    def _handle_pause_task(self):
        _logger.debug('CMD_PAUSE_MOVEMENT')
        if self._movement_task.state in [
            main_pb2.MovementTask.MT_RUNNING,
            main_pb2.MovementTask.MT_WAIT_FOR_START,
        ]:
            self._movement_task.state = main_pb2.MovementTask.MT_PAUSED
            self._sys_state = main_pb2.SystemState.SYS_STATE_TASK_MANUAL_PAUSED
        if self._action_task.state in [
            main_pb2.ActionTask.AT_RUNNING,
            main_pb2.ActionTask.AT_WAIT_FOR_START,
        ]:
            self._action_task.state = main_pb2.ActionTask.AT_PAUSED

    def _handle_continue_task(self):
        _logger.debug('CMD_CONTINUE_MOVEMENT')
        if self._movement_task.state == main_pb2.MovementTask.MT_PAUSED:
            self._movement_task.state = main_pb2.MovementTask.MT_RUNNING
            self._sys_state = main_pb2.SystemState.SYS_STATE_TASK_NAV_WAITING_FINISH
        if self._action_task.state == main_pb2.ActionTask.AT_PAUSED:
            self._action_task.state = main_pb2.ActionTask.AT_RUNNING

    def _handle_cancel_task(self):
        _logger.debug('CMD_COMMON_CANCEL')
        if self._movement_task.state in [
            main_pb2.MovementTask.MT_RUNNING,
            main_pb2.MovementTask.MT_WAIT_FOR_START,
            main_pb2.MovementTask.MT_PAUSED,
        ]:
            self._movement_task.result = main_pb2.TASK_RESULT_CANCELED
            self._movement_task.state = main_pb2.MovementTask.MT_FINISHED
            self._sys_state = main_pb2.SystemState.SYS_STATE_IDLE
        if self._action_task.state in [
            main_pb2.ActionTask.AT_RUNNING,
            main_pb2.ActionTask.AT_WAIT_FOR_START,
            main_pb2.ActionTask.AT_PAUSED,
        ]:
            self._action_task.result = main_pb2.TASK_RESULT_CANCELED
            self._action_task.state = main_pb2.ActionTask.AT_FINISHED

    def _handle_replace_move_path(self, paths: list):
        _logger.debug(f'CMD_PATH_REPLACE {paths}')
        if self._movement_task.state not in [
            main_pb2.MovementTask.MT_RUNNING,
            main_pb2.MovementTask.MT_PAUSED,
        ]:
            _logger.error(f'当前任务没有启动，不允许替换路径 {self._movement_task.state}')
            return
        del self._movement_task.paths[:]
        self._movement_task.paths.extend(paths)

    def _handle_running_movement_task(self):
        if self._movement_task.state in (
            main_pb2.MovementTask.MT_FINISHED,
            main_pb2.MovementTask.MT_NA,
        ):
            self._cur_v = 0
            return

        if self._movement_task.state == main_pb2.MovementTask.MT_WAIT_FOR_START:
            self._movement_task.state = main_pb2.MovementTask.MT_RUNNING
            self._sys_state = main_pb2.SystemState.SYS_STATE_TASK_NAV_WAITING_FINISH
        elif self._movement_task.state == main_pb2.MovementTask.MT_PAUSED:
            self._cur_v = 0
            return

        paths = self._movement_task.paths
        if self._movement_task.cur_path_no == 0:
            _logger.debug('cur_path_no change: 0 -> 1')
            self._movement_task.cur_path_no = 1
        curr_path = paths[self._movement_task.cur_path_no - 1]
        self._cur_v = curr_path.limit_v

        def to_native_path(path):
            native_path = Path()
            native_path.type = PathType(path.type)
            native_path.direction = Direction(path.direction)
            native_path.sx = path.sx
            native_path.sy = path.sy
            native_path.cx = path.cx
            native_path.cy = path.cy
            native_path.dx = path.dx
            native_path.dy = path.dy
            native_path.ex = path.ex
            native_path.ey = path.ey
            native_path.rotate_angle = path.rotate_angle
            native_path.radius = path.radius
            native_path.limit_v = path.limit_v
            native_path.limit_w = path.limit_w

            return native_path

        curr_path = to_native_path(curr_path)

        if curr_path.type == main_pb2.Path.PATH_LINE:
            point = move_to_target_at_line(
                curr_path, self._curr_pose.point() * 1000, MOVE_STEP * 1000
            )
            self._curr_pose.set_point(point / 1000)
            # 机器人走直线的时候朝向会跟随直线朝向(同时考虑移动时方向)
            self._curr_pose.yaw = curr_path.end_facing()
            if self._curr_pose.point().is_same_point(
                Point(curr_path.ex / 1000, curr_path.ey / 1000)
            ):
                self._handle_next_path()
        elif curr_path.type == main_pb2.Path.PATH_ROTATE:
            target_angle = math.degrees(curr_path.rotate_angle / 1000)
            self._curr_pose.yaw = rotate_to_target(self._curr_pose.yaw, target_angle, ROTATE_STEP)
            if AngleUtils.equal_norm(self._curr_pose.yaw, target_angle, ANGLE_ACCEPT_DIFF):
                self._handle_next_path()
        elif curr_path.type == main_pb2.Path.PATH_BEZIER:
            pose, self._curr_bezier_t = move_to_target_at_bezier(
                curr_path, self._curr_bezier_t, MOVE_STEP * 1000
            )
            self._curr_pose.set_point(pose.point() / 1000)
            self._curr_pose.yaw = pose.yaw
            if self._curr_bezier_t >= 1:
                self._curr_bezier_t = 0.0
                self._handle_next_path()
        else:
            raise NotImplementedError(f'未实现的路径路径类型：{curr_path.type}')

        # 执行移动过程中，动作控制器也需要处理相关逻辑，如：开同步旋转过程中，底盘旋转对于的顶板也需要相对旋转
        self._actuator.handle_running_movement_task(self._curr_pose)

        if self._movement_task.state == main_pb2.MovementTask.MT_FINISHED:
            self._movement_task.remain_distance = 0
        else:
            dist = math.dist(
                [self._curr_pose.x, self._curr_pose.y], [paths[-1].ex / 1000, paths[-1].ey / 1000]
            )
            self._movement_task.remain_distance = int(dist * 100)

    def _handle_cancel_movement_task(self, soft_cancel: bool):
        if self._movement_task.state in [
            main_pb2.MovementTask.MT_RUNNING,
            main_pb2.MovementTask.MT_WAIT_FOR_START,
            main_pb2.MovementTask.MT_PAUSED,
        ]:
            self._movement_task.result = main_pb2.TASK_RESULT_CANCELED
            self._movement_task.state = main_pb2.MovementTask.MT_FINISHED
            self._sys_state = main_pb2.SystemState.SYS_STATE_IDLE

    def _handle_next_path(self):
        paths = self._movement_task.paths
        if len(paths) == self._movement_task.cur_path_no:
            self._movement_task.result = main_pb2.TASK_RESULT_OK
            self._movement_task.state = main_pb2.MovementTask.MT_FINISHED
            self._sys_state = main_pb2.SystemState.SYS_STATE_IDLE
            if self._callback_move_task_finish is not None:
                self._callback_move_task_finish(self._movement_task)
        else:
            _logger.debug(
                f'cur_path_no change: {self._movement_task.cur_path_no} -> '
                f'{self._movement_task.cur_path_no + 1}'
            )
            self._movement_task.cur_path_no += 1

    def _handle_running_action_task(self):
        if self._action_task.state in (
            main_pb2.ActionTask.AT_FINISHED,
            main_pb2.ActionTask.AT_ZERO,
        ):
            return

        if self._action_task.state == main_pb2.ActionTask.AT_WAIT_FOR_START:
            self._action_task.state = main_pb2.ActionTask.AT_RUNNING
        elif self._action_task.state == main_pb2.ActionTask.AT_PAUSED:
            return

        self._actuator.handle_running_action_task(self._curr_pose)

    def _update_system_state(self):
        self._req_seq += 1
        rotate_value = 0
        sync_rotate = False
        if self.actuator_type == ActuatorType.Lift_Rotate:
            rotate_value = int(math.radians(self._actuator.rotate_value) * 1000)
            sync_rotate = self._actuator.sync_rotate
        self.system_state = main_pb2.SystemState(
            req_seq=self._req_seq,
            sys_state=self._sys_state,
            operation_state=self._operation_state,
            location_state=self._location_state,
            location_pose=main_pb2.Pose(
                x=int(self._curr_pose.x * 1000),
                y=int(self._curr_pose.y * 1000),
                yaw=int(math.radians(self._curr_pose.yaw) * 1000),
            ),
            mc_state=main_pb2.MotionControlState(
                v_x=self._cur_v,  # 似乎不区分 xy 方向速度，统一用的 v_x
            ),
            movement_state=self._movement_task,
            action_state=self._action_task,
            map_name=self._map_name,
            rotate_value=rotate_value,
            load_state=self._actuator.load_state,
            multi_load_state=self._actuator.multi_load_state,
            sync_rotate=sync_rotate,
            emergency_state=main_pb2.SystemState.STATE_EMERGENCY_NONE,
        )
        if self._callback_system_state is not None:
            self._callback_system_state(self.system_state)

    def _update_hardware_state(self):
        # 充电 20min 充满，续航 24h
        if self._battery_state == main_pb2.HardwareState.BATTERY_CHARGING:
            self.battery_remain_capacity += self.battery_nominal_capacity / (
                20 * 60 / LOOP_INTERVAL
            )
        else:
            self.battery_remain_capacity -= self.battery_nominal_capacity / (
                24 * 3600 / LOOP_INTERVAL
            )

        # 限制剩余电量范围: (1%, 100%)
        if self.battery_remain_capacity > self.battery_nominal_capacity:
            self.battery_remain_capacity = self.battery_nominal_capacity
        elif self.battery_remain_capacity < self.battery_nominal_capacity / 100:
            self.battery_remain_capacity = self.battery_nominal_capacity / 100

        self.hardware_state = main_pb2.HardwareState(
            req_seq=self._req_seq,
            cpu_usage=10,
            memory_usage=20,
            disk_usage=30,
            remain_disk_space=5 * 1024,
            wifi_state=main_pb2.HardwareState.WIFI_NA,
            break_sw_state=self._break_sw_state,
            battery_state=self._battery_state,
            battery_temperature=28,
            battery_current=560,
            battery_voltage=52940,
            battery_percentage=round(
                100 * self.battery_remain_capacity / self.battery_nominal_capacity
            ),
            battery_nominal_capacity=int(self.battery_nominal_capacity),
            battery_remain_capacity=int(self.battery_remain_capacity),
            power_state=main_pb2.HardwareState.POWER_NORMAL,
            laser_state=main_pb2.HardwareState.LASER_OK,
            hardware_state=main_pb2.HardwareState.H_STATE_OK,
        )
        if self._callback_hardware_state is not None:
            self._callback_hardware_state(self.hardware_state)

    def _update_sensor_samples(self):
        NoiseSensor = monitor_pb2.NoiseSensor
        LoadUnitSensor = monitor_pb2.LoadUnitSensor

        # TODO(zZ): 生成采样数据
        self.sensor_samples = monitor_pb2.SensorDataCollection(
            noise_1=[
                NoiseSensor(timestamp_us=int(time.time() * 1e6 - 3e4), noise_db=43),
                NoiseSensor(timestamp_us=int(time.time() * 1e6), noise_db=42),
            ],
            loadunit_1=[
                LoadUnitSensor(timestamp_us=int(time.time() * 1e6 - 6e4), offset_m=0.2),
                LoadUnitSensor(timestamp_us=int(time.time() * 1e6 - 3e4), offset_m=0.04),
                LoadUnitSensor(timestamp_us=int(time.time() * 1e6), weight_kg=20),
            ],
        )
        if self._callback_sensor_samples:
            self._callback_sensor_samples(self.sensor_samples)

    def assert_new_path_start_path_is_valid(self, paths):
        assert paths, '路径不能为空'
        if paths[0].type != PathType.PATH_ROTATE:
            begin_facing: float = paths[0].begin_facing()
            diff = AngleUtils.delta_norm(begin_facing, self._curr_pose.yaw)
            assert diff < 4, (
                f'起始朝向和车头朝向差别过大,diff:{diff:.3f}, begin_facing:{begin_facing:.3f}, '
                f'cur yaw:{self._curr_pose.yaw:.3f} {paths[0]}'
            )

            # 旋转路径的 sx, sy 均为 0
            diff = math.dist([paths[0].sx / 1000, paths[0].sy / 1000], self._curr_pose.point())
            assert diff <= 0.1, (
                f'起始路径偏差过大：{diff:.3f}, {self._curr_pose.point()}, '
                f'{[paths[0].sx / 1000, paths[0].sy / 1000]}'
            )

    def assert_new_paths_is_valid(self, paths):
        paths_size = len(paths)
        for i in range(paths_size - 1):
            j = i + 1
            if paths[j].type != PathType.PATH_ROTATE:
                diff = AngleUtils.delta_norm(paths[i].end_facing(), paths[j].begin_facing())
                assert diff < 4, (
                    f'连续路径的朝向不一致,diff:{diff:.3f} path{i} end facing:{paths[i].end_facing():.3f}, '
                    f'path{j} begin facing:{paths[j].begin_facing():.3f}'
                )

        for i in range(paths_size - 1):
            if paths[i].type == PathType.PATH_ROTATE:
                continue
            for j in range(i + 1, paths_size):
                if paths[j].type == PathType.PATH_ROTATE:
                    continue
                else:
                    diff = math.dist([paths[i].ex, paths[i].ey], [paths[j].sx, paths[j].sy])
                    assert diff < 0.5 * 1000, (
                        f'路径间距离过大：{diff:.3f}, path{i} end point:{paths[i].ex, paths[i].ey}, '
                        f'path{j} start point:{paths[j].sx, paths[j].sy}'
                    )
                    break


if __name__ == '__main__':
    from protocol_adapter.utils import SrosLog

    sros_log = SrosLog('')
    sros_log.sendLogToConsole()

    sros = SrosMock()
    sros.run()
    sros.execute_action_task(1, 133, 1, 0)
