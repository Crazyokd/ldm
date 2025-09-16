# Copyright 2024 Standard Robots Co. All rights reserved.
# 若没特殊说明，单位统一用角度和米,角度[0, 360)
from protocol_adapter.mock.actuator_mock import ActuatorMock
from protocol_adapter.protobuf_wrapper import main_pb2
from protocol_adapter.protobuf_wrapper.base import Pose


class RollerActuatorMock(ActuatorMock):
    def __init__(self, loop_interval: float):
        super().__init__(loop_interval)

    def _handle_running_movement_task(self, curr_pose: Pose):
        pass

    def _handle_running_action_task(self, curr_pose: Pose):
        if self._action_task.id != 192 and self._action_task.param0 != 1:
            raise AssertionError(f'本机构不支持此动作：{self._action_task}')

        if self._action_task.param1 == 11:
            self._handle_192_1_11(curr_pose)
        elif self._action_task.param1 == 12:
            self._handle_192_1_12(curr_pose)
        else:
            raise AssertionError(f'本机构不支持此动作：{self._action_task}')

    def _handle_192_1_11(self, curr_pose: Pose):
        ACTION_NEED_RUNNING_INTERVAL = 0.5
        if self._action_running_interval >= ACTION_NEED_RUNNING_INTERVAL:
            self.load_state = main_pb2.SystemState.LOAD_FULL
            self.multi_load_state = 1
            self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _handle_192_1_12(self, curr_pose: Pose):
        ACTION_NEED_RUNNING_INTERVAL = 0.5
        if self._action_running_interval >= ACTION_NEED_RUNNING_INTERVAL:
            self.load_state = main_pb2.SystemState.LOAD_FREE
            self.multi_load_state = 0
            self._action_task_finish(main_pb2.TASK_RESULT_OK)
