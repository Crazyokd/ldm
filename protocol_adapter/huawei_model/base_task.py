import abc

from protocol_adapter.models.task import TaskState, TaskType, TaskItem

from protocol_adapter.huawei_model.base import Base
from protocol_adapter.huawei_model.const import get_int_dat, MoveType


#                                           BaseTask
#                                              |
#                                           MoveTask
#                                              |
#                            ---------------------------------------
#                            |                                     |
#                      LinearMoveTask                           ArcMoveTask


class BaseTask(Base):
    def __init__(self, task_type=TaskType.Unknown):
        super().__init__()
        self.task_type = task_type
        # 一个完整任务，如导航到指定位置，顶起货架，带货架导航到目标位置，放下货架，任务id是相同的
        # 但是每一个子任务id不同
        self.task_id = 0
        self.sub_task_id = 0
        self.move_type = MoveType.Forward
        self.task_detail = TaskItem.Normal  # 大任务类型
        self.is_execute_action_when_move = False  # 移动过程中是否同步执行执行机构动作
        self.actuator_info = None  # 执行机构信息
        self.charge_info = None
        self.state = TaskState.NONE

    def get_task_id(self):
        return self.task_id, self.sub_task_id

    def get_task_id_str(self):
        return f'{self.task_id}.{self.sub_task_id}'

    def is_same_task_id(self, task_id, sub_task_id):
        return self.task_id == task_id and self.sub_task_id == sub_task_id

    # 是否动态识别货架腿
    def is_auto_identify_shelf_leg(self):
        return self.task_detail == TaskItem.Shelf_Leg_Identify

    @abc.abstractmethod
    def from_dat(self, dat):
        self.task_id = get_int_dat(dat, 4, 2, signed=False)
        self.sub_task_id = get_int_dat(dat, 6, 1, signed=False)
        self.move_type = get_int_dat(dat, 7, 1)
        self.task_detail = get_int_dat(dat, 8, 2)
        self.is_execute_action_when_move = get_int_dat(dat, 10, 1) == 1

    def is_move_backward(self):
        return self.move_type in (
            MoveType.Backward,
            MoveType.Backward_Rad,
            MoveType.Backward_Bias,
        )

    def is_move_still(self):
        return self.move_type == MoveType.Still

    # 是否是充电任务，包括启动充电和停止充电
    def is_charge_task(self):
        return self.task_type == TaskType.Charge_Task

    def is_start_charge(self):
        if not self.is_charge_task():
            return False
        if self.charge_info:
            return self.charge_info.is_start_charge()
        else:
            return False

    def is_stop_charge(self):
        if not self.is_charge_task():
            return False
        if self.charge_info:
            return self.charge_info.is_stop_charge()
        else:
            return False

    def get_charge_time_in_second(self):
        if not self.is_charge_task() or not self.charge_info:
            return 0
        return self.charge_info.get_charge_time_in_second()

    # 是否是移动任务
    def is_task_type_no_payload_linear_move(self):
        return self.task_type == TaskType.No_Payload_Linear_Move

    def is_task_type_slam_nav(self):
        return self.task_type == TaskType.Slam_Nav

    def is_task_type_raise_shelf_only(self):
        return self.task_type == TaskType.Raise_Shelf_Action

    def is_task_type_put_shelf_only(self):
        return self.task_type == TaskType.Put_Shelf_Action

    def is_task_type_linear_move_after_raise_shelf(self):
        return self.task_type == TaskType.Linear_Move_After_Raise_Shelf

    def is_task_type_linear_move_after_put_shelf(self):
        return self.task_type == TaskType.Linear_Move_After_Put_Shelf

    def is_task_type_no_payload_arc_move(self):
        return self.task_type == TaskType.No_Payload_Arc_Move

    def is_task_type_arc_move_after_raise_shelf(self):
        return self.task_type == TaskType.Arc_Move_After_Raise_Shelf

    def is_task_type_arc_move_after_put_shelf(self):
        return self.task_type == TaskType.Arc_Move_After_Put_Shelf

    def is_task_type_shelf_sn_detect(self):
        return self.task_type == TaskType.Shelf_SN_Detect

    # 是否是货架任务
    def is_task_type_shelf(self):
        return (
            self.is_task_type_raise_shelf_only()
            or self.is_task_type_put_shelf_only()
            or self.is_task_type_move_after_raise_shelf()
            or self.is_task_type_move_after_put_shelf()
        )

    def is_task_type_smt_move(self):
        return self.task_type in (
            TaskType.Multi_Path_No_Payload_Move,
            TaskType.Smt_Multi_Path_Move,
        )

    def is_task_type_smt_action(self):
        return self.task_type in (
                TaskType.Smt_Load_Action,
                TaskType.Smt_Unload_Action,
            )

    def is_task_type_smt(self):
        return self.is_task_type_smt_move() or self.is_task_type_smt_action()

    def is_task_detail_fork(self):
        return self.task_detail in (
            TaskItem.Fork_load_Action_Go_DOCK,
            TaskItem.Fork_Load_Action_Go_Back,
            TaskItem.Fork_Unload_Action_Go_Back,
            TaskItem.Fork_Unload_Action_Go_DOCK,
        )

    def is_task_type_arm_load_action(self):
        return not self.is_task_detail_fork() and self.task_type == TaskType.Arm_Fork_Load_Action

    def is_task_type_arm_unload_action(self):
        return not self.is_task_detail_fork() and self.task_type == TaskType.Arm_Fork_Unload_Action

    def is_task_type_arm_action(self):
        return self.is_task_type_arm_load_action() or self.is_task_type_arm_unload_action()

    def is_task_type_fork_load_action(self):
        return self.is_task_detail_fork() and self.task_type == TaskType.Arm_Fork_Load_Action

    def is_task_type_fork_load_action_move_back(self):
        return (
            self.is_task_detail_fork()
            and self.task_type == TaskType.Multi_Path_Move_After_Raise_Shelf
            and self.task_detail == TaskItem.Fork_Load_Action_Go_Back
        )

    def is_task_type_fork_unload_action(self):
        return self.is_task_detail_fork() and self.task_type == TaskType.Arm_Fork_Unload_Action

    def is_task_type_fork_unload_action_move_back(self):
        return (
            self.is_task_detail_fork()
            and self.task_type == TaskType.Multi_Path_No_Payload_Move
            and self.task_detail == TaskItem.Fork_Unload_Action_Go_Back
        )

    def is_task_type_fork_action(self):
        return (
            self.is_task_type_fork_load_action()
            or self.is_task_type_fork_load_action_move_back()
            or self.is_task_type_fork_unload_action()
            or self.is_task_type_fork_unload_action_move_back()
        )

    def is_task_type_move_after_raise_shelf(self):
        return (
            self.is_task_type_linear_move_after_raise_shelf()
            or self.is_task_type_arc_move_after_raise_shelf()
            or self.is_task_type_multi_move_after_raise_shelf()
        )

    def is_task_type_move_after_put_shelf(self):
        return (
            self.is_task_type_linear_move_after_put_shelf()
            or self.is_task_type_arc_move_after_put_shelf()
            or self.is_task_type_multi_move_after_put_shelf()
        )

    def is_task_raise_shelf(self):
        return self.is_task_type_raise_shelf_only()

    def is_task_put_shelf(self):
        return self.is_task_type_put_shelf_only() or self.is_task_type_move_after_put_shelf()

    def is_task_type_roller(self):
        return self.task_type == TaskType.Roller_Control

    def is_task_linear_move(self):
        return (
            self.is_task_type_no_payload_linear_move()
            or self.is_task_type_slam_nav()
            or self.is_charge_task()
            or self.is_task_type_linear_move_after_raise_shelf()
            or self.is_task_type_shelf_sn_detect()
        )

    def is_task_arc_move(self):
        return (
            self.is_task_type_arc_move_after_raise_shelf()
            or self.is_task_type_no_payload_arc_move()
        )

    def is_task_type_nopyload_multi_path_move(self):
        return self.task_type == TaskType.Multi_Path_No_Payload_Move

    def is_task_type_multi_move_after_raise_shelf(self):
        return self.task_type == TaskType.Multi_Path_Move_After_Raise_Shelf

    def is_task_type_multi_move_after_put_shelf(self):
        return self.task_type == TaskType.Multi_Path_Move_After_Put_Shelf

    def is_task_type_with_multi_path_move(self):
        return (
            self.is_task_type_nopyload_multi_path_move()
            or self.is_task_type_multi_move_after_raise_shelf()
            or self.is_task_type_multi_move_after_put_shelf()
            or self.is_task_type_arm_action()
            or self.is_task_type_smt()
        )

    def is_task_movement(self):
        return (
            self.is_task_linear_move()
            or self.is_task_arc_move()
            or self.is_task_type_with_multi_path_move()
        )

    def is_task_movement_mini(self):
        """是否是最小化的移动类任务，暂用于限制修改影响范围：
        1. 任务id变更时，仅此类集合，允许取消旧任务切新任务
        2. 任务完成时，对此类集合，在完成后上报几帧任务完成状态
        """
        return self.task_type in (
            TaskType.No_Payload_Linear_Move,
            TaskType.No_Payload_Arc_Move,
            TaskType.Linear_Move_After_Raise_Shelf,
            TaskType.Linear_Move_After_Put_Shelf,
            TaskType.Arc_Move_After_Raise_Shelf,
            TaskType.Arc_Move_After_Put_Shelf,
            TaskType.Multi_Path_No_Payload_Move,
            TaskType.Multi_Path_Move_After_Raise_Shelf,
            TaskType.Multi_Path_Move_After_Put_Shelf,
            TaskType.Smt_Multi_Path_Move,
            TaskType.Smt_Load_Action,
            TaskType.Smt_Unload_Action,
            TaskType.Slam_Nav,
        )

    def is_task_execute_repeatable(self):
        return (
            self.is_task_movement()
            or self.is_task_type_shelf_sn_detect()
            or self.is_task_put_shelf()
            or self.is_task_raise_shelf()
            or self.is_task_type_fork_action()
        )

    def is_task_action(self):
        return (
            self.is_task_type_roller()
            or self.is_task_type_raise_shelf_only()
            or self.is_task_put_shelf()
        )

    # 判断是否是重复任务
    def is_duplicated_task(self, task):
        return False

    def __str__(self):
        result = (
            f'Task: {self.task_id}.{self.sub_task_id} ('
            f'task_type: {self.task_type:#x}, '
            f'move_type: {self.move_type}, '
            f'task_detail: {self.task_detail}, '
            f'is_execute_action_when_move: {self.is_execute_action_when_move})'
        )
        if self.actuator_info is not None:
            if isinstance(self.actuator_info, list):
                result += '\n  roll info: [{}]'.format(
                    ','.join(x.__str__() for x in self.actuator_info)
                )
            else:
                result += f'\n  actuatorInfo: [{self.actuator_info}]'

        if self.charge_info:
            result += f'\n  chargeInfo: {self.charge_info}'
        return result
