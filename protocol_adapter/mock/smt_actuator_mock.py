from protocol_adapter.const import ActionID
from protocol_adapter.huawei_model.const import SmtActionDirection
from protocol_adapter.huawei_model.smt_info import SmtState
from protocol_adapter.mock.actuator_mock import ActuatorMock
from protocol_adapter.protobuf_wrapper.base import Pose
from protocol_adapter.protobuf_wrapper import main_pb2


class SmtActuatorMock(ActuatorMock):
    def __init__(self, loop_interval: float):
        super().__init__(loop_interval)

        self.state = SmtState()

        self.unit_0 = self.state.units[0]

    def _handle_running_movement_task(self, curr_pose: Pose):
        pass

    def _handle_running_action_task(self, curr_pose: Pose):
        if self._action_task.id == ActionID.EAC:
            if self._action_task.param0 in (1, 2, 21, 22, 100, 201, 204, 205):
                getattr(self, f'_handle_192_{self._action_task.param0}_x')(self._action_task.param1)
            else:
                raise AssertionError(
                    f'本机构不支持此动作：192.{self._action_task.param0}.{self._action_task.param1}'
                )
        else:
            self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _update_on_load_unload(self, x):
        if x not in (3, 4):
            raise AssertionError(
                f'未定义的动作：192.{self._action_task.param0}.{self._action_task.param1}'
            )

        unit = self.unit_0
        if self._action_running_interval < 0.5:
            unit.cargo_state = 2
            unit.docking_state = 1
            if x == 3:
                unit.action_type = 2
            if x == 4:
                unit.action_type = 1
        else:
            if x == 3:
                unit.cargo_state = 1
            elif x == 4:
                unit.cargo_state = 0

            unit.action_type = 0
            self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _handle_192_1_x(self, x):
        unit = self.unit_0
        unit.action_direction = SmtActionDirection.Left.value
        self._update_on_load_unload(x)

    def _handle_192_2_x(self, x):
        unit = self.unit_0
        unit.action_direction = SmtActionDirection.Right.value
        self._update_on_load_unload(x)

    def _handle_192_21_x(self, x):
        unit = self.unit_0
        # 重置对接状态
        unit.docking_state = 0

        if unit.lift_height != x:
            unit.lift_speed = 400

            # 向上移动
            if unit.lift_height < x:
                unit.lift_height += int(self._loop_interval * unit.lift_speed)
                unit.lift_height = min(unit.lift_height, x)

            # 向上移动
            if unit.lift_height > x:
                unit.lift_height -= int(self._loop_interval * unit.lift_speed)
                unit.lift_height = max(unit.lift_height, x)

        if unit.lift_height != x:
            unit.action_type = 3
        else:
            unit.action_type = 0
            unit.lift_speed = 0
            self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _handle_192_22_x(self, x):
        unit = self.unit_0
        unit.docking_state = 0
        unit.cargo_type = x
        unit.adjust_width_speed = 50
        if self._action_running_interval < 0.3:
            unit.action_type = 4
        else:
            unit.action_type = 0
            unit.adjust_width_speed = 0
            self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _handle_192_100_x(self, x):
        unit = self.unit_0
        unit.docking_state = 0
        unit.action_direction = 0
        if self._action_running_interval < 0.6:
            unit.action_type = 5
        else:
            unit.action_type = 0
            self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _handle_192_201_x(self, x):
        if x not in (1, 2, 11, 12):
            raise AssertionError(
                f'未定义的动作：192.{self._action_task.param0}.{self._action_task.param1}'
            )
        if self._action_running_interval >= 0.6:
            self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _handle_192_204_x(self, x):
        unit = self.unit_0

        if x == 1:
            unit.action_direction = SmtActionDirection.Left.value
        elif x == 2:
            unit.action_direction = SmtActionDirection.Right.value
        else:
            raise AssertionError(
                f'未定义的动作：192.{self._action_task.param0}.{self._action_task.param1}'
            )

        if self._action_running_interval < 0.6:
            unit.docking_state = 1
        else:
            self._action_task_finish(main_pb2.TASK_RESULT_OK)

    def _handle_192_205_x(self, x):
        unit = self.unit_0
        if self._action_running_interval < 0.6:
            unit.docking_state = 1
        else:
            if x == 0:
                unit.docking_state = 2
                unit.action_direction = 0
            self._action_task_finish(main_pb2.TASK_RESULT_OK)
