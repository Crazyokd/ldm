# Copyright 2024 Standard Robots Co. All rights reserved.
import logging

from abc import ABC, abstractmethod

from protocol_adapter.protobuf_wrapper import main_pb2
from protocol_adapter.protobuf_wrapper.base import Pose

_logger = logging.getLogger(__name__)


class ActuatorMock(ABC):
    def __init__(self, loop_interval: float):
        super().__init__()
        self._callback_action_task_finish = None
        self._loop_interval: float = loop_interval
        self._action_running_interval = 0
        self._action_task = main_pb2.ActionTask()
        self.load_state = main_pb2.SystemState.LOAD_FREE
        self.multi_load_state: int = 0

    def set_action(self, action_task):
        self._action_running_interval = 0
        self._action_task = action_task

    def set_notify_action_task_finished_callback(self, fun):
        self._callback_action_task_finish = fun

    def handle_running_movement_task(self, curr_pose: Pose):
        """移动任务每个周期更新都会调用此函数，可以做一些和移动强相关的动作,如：同步旋转"""
        self._handle_running_movement_task(curr_pose)

    def handle_running_action_task(self, curr_pose: Pose):
        """动作任务每个周期都会调用此函数
        curr_pose为当前车辆坐标，可以被动作任务修改，如：顶升后车辆会位置会跟随货架位置"""
        self._action_running_interval += self._loop_interval
        self._handle_running_action_task(curr_pose)

    @abstractmethod
    def _handle_running_movement_task(self, curr_pose: Pose):
        pass

    @abstractmethod
    def _handle_running_action_task(self, curr_pose: Pose):
        pass

    def _action_task_finish(
        self, result: main_pb2.TaskResult, result_code: int = 0, result_str: str = ''
    ) -> None:
        self._action_task.result = result
        self._action_task.result_code = result_code
        self._action_task.result_str = result_str
        self._action_task.state = main_pb2.ActionTask.AT_FINISHED
        if self._callback_action_task_finish is not None:
            self._callback_action_task_finish(self._action_task)
        _logger.debug(f'动作任务完成：{self._action_task}')
