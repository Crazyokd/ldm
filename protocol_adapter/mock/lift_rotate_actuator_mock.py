# Copyright 2024 Standard Robots Co. All rights reserved.
# 若没特殊说明，单位统一用角度和米,角度[0, 360)
from protocol_adapter.utils import AngleUtils
from protocol_adapter.mock.actuator_mock import ActuatorMock
from protocol_adapter.mock.world_mock import WorldMock
from protocol_adapter.protobuf_wrapper.base import rotate_to_target, Pose
from protocol_adapter.protobuf_wrapper import main_pb2


SRL_ROTATE_SPEED = 30  # per seconds


class LiftRotateActuatorMock(ActuatorMock):
    def __init__(self, loop_interval: float):
        super().__init__(loop_interval)
        self._rotate_speed = SRL_ROTATE_SPEED * self._loop_interval  # 顶板的旋转速度
        self.rotate_value: float = 0  # 单位度
        self.sync_rotate: bool = False
        self.shelf_id: str = ''

    def _handle_running_movement_task(self, curr_pose: Pose):
        if self.load_state == main_pb2.SystemState.LOAD_FULL:
            world = WorldMock()
            if self.sync_rotate:
                world.set_shelf_point(self.shelf_id, curr_pose.point())
                _, shelf_pose = world.get_shelf_by_point(curr_pose.point())
                self.rotate_value = AngleUtils.normalize_360(shelf_pose.yaw - curr_pose.yaw)
            else:
                world.set_shelf_point(self.shelf_id, curr_pose.point())
                world.set_shelf_angle(
                    self.shelf_id, AngleUtils.normalize_360(self.rotate_value + curr_pose.yaw)
                )

    def _handle_running_action_task(self, curr_pose: Pose):
        if self._action_task.id == 4:
            if self._action_task.param0 == 1:
                self._handle_4_1_0(curr_pose)
            elif self._action_task.param0 == 2:
                self._handle_4_2_0()
            elif self._action_task.param0 == 5:
                self._handle_4_5_0(curr_pose)
            elif self._action_task.param0 == 11:
                self._handle_4_11_x(curr_pose)
            elif self._action_task.param0 == 12:
                self._handle_4_12_x(curr_pose)
            elif self._action_task.param0 == 13:
                self.sync_rotate = True
                self._action_task_finish(main_pb2.TASK_RESULT_OK)
            elif self._action_task.param0 == 14:
                self.sync_rotate = False
                self._action_task_finish(main_pb2.TASK_RESULT_OK)
        elif self._action_task.id == 133:
            if self._action_task.param0 == 1:
                self._handle_133_1_x(curr_pose)
        else:
            assert False, f'本机构不支持此动作类型：{self._action_task.id}'

    def _handle_4_1_0(self, curr_pose: Pose):
        ACTION_NEED_RUNNING_INTERVAL = 0.5
        world = WorldMock()
        shelf_id, shelf_pose = world.get_shelf_by_point(curr_pose.point())
        if not shelf_id:
            self._action_task_finish(main_pb2.TASK_RESULT_FAILED, 400403)
            return

        if self._action_running_interval >= ACTION_NEED_RUNNING_INTERVAL:
            self.load_state = main_pb2.SystemState.LOAD_FULL
            self.shelf_id = shelf_id
            # 定起货架后，车和货架的位置一致
            curr_pose.x = shelf_pose.x
            curr_pose.y = shelf_pose.y
            curr_pose.yaw = shelf_pose.yaw
            self.rotate_value = 0
            self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _handle_4_2_0(self):
        ACTION_NEED_RUNNING_INTERVAL = 0.5
        if self.load_state != main_pb2.SystemState.LOAD_FULL:
            self._action_task_finish(main_pb2.TASK_RESULT_FAILED)
            return

        if self._action_running_interval >= ACTION_NEED_RUNNING_INTERVAL:
            self.load_state = main_pb2.SystemState.LOAD_FREE
            self.shelf_id = ''
            self.rotate_value = 0
            self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _handle_4_5_0(self, curr_pose: Pose):
        ACTION_NEED_RUNNING_INTERVAL = 0.5
        world = WorldMock()
        shelf_id, shelf_pose = world.get_shelf_by_point(curr_pose.point())
        if not shelf_id:
            self._action_task_finish(main_pb2.TASK_RESULT_FAILED, 400403)
            return

        if self._action_running_interval >= ACTION_NEED_RUNNING_INTERVAL:
            if AngleUtils.delta_norm(shelf_pose.yaw, curr_pose.yaw) <= 5:
                self.load_state = main_pb2.SystemState.LOAD_FULL
                self.shelf_id = shelf_id
                curr_pose.x, curr_pose.y = shelf_pose.x, shelf_pose.y
                self.rotate_value = 0
                self._action_task_finish(main_pb2.TASK_RESULT_OK)
            else:
                self._action_task_finish(main_pb2.TASK_RESULT_FAILED)

    def _handle_4_11_x(self, curr_pose: Pose):
        ACTION_NEED_RUNNING_INTERVAL = 0.5
        if self._action_running_interval < ACTION_NEED_RUNNING_INTERVAL:
            return

        world = WorldMock()
        shelf_id, _ = world.get_shelf_by_point(curr_pose.point())

        target_hight = float(self._action_task.param1) / 10

        if self.load_state != main_pb2.SystemState.LOAD_FULL and target_hight > 5 and shelf_id:
            self.load_state = main_pb2.SystemState.LOAD_FULL
            self.shelf_id = shelf_id

        elif self.load_state == main_pb2.SystemState.LOAD_FULL and target_hight == 0:
            self.load_state = main_pb2.SystemState.LOAD_FREE
            self.shelf_id = ''

        self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _handle_4_12_x(self, curr_pose: Pose):
        target_angle = float(self._action_task.param1) / 10
        self.rotate_value = rotate_to_target(self.rotate_value, target_angle, self._rotate_speed)
        # 载货时才转货架
        if self.load_state == main_pb2.SystemState.LOAD_FULL:
            world = WorldMock()
            world.set_shelf_angle(
                self.shelf_id, AngleUtils.normalize_360(self.rotate_value + curr_pose.yaw)
            )
        if AngleUtils.equal_norm(target_angle, self.rotate_value, 1):
            self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _handle_133_1_x(self, curr_pose: Pose):
        world = WorldMock()
        shelf_id, _ = world.get_shelf_by_point(curr_pose.point())
        if shelf_id:
            self._action_task_finish(main_pb2.TASK_RESULT_OK, 0, shelf_id)
            return

        if (
            self._action_task.param1 == 0
            or self._action_running_interval >= self._action_task.param1
        ):
            self._action_task_finish(main_pb2.TASK_RESULT_FAILED, 0, '')
