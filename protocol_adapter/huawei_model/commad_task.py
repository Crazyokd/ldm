import abc

from protocol_adapter.models.task import TaskType
from protocol_adapter.huawei_model.base_task import BaseTask
from protocol_adapter.huawei_model.const import get_int_dat


# 处理暂停、继续、停车、取消等命令型任务
class CommandTask(BaseTask):
    def __init__(self, task_type=TaskType.Unknown):
        super().__init__(task_type)

    @abc.abstractmethod
    def from_dat(self, dat):
        self.task_id = get_int_dat(dat, 4, 2, signed=False)
        self.sub_task_id = get_int_dat(dat, 6, 1, signed=False)
