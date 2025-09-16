#!/usr/bin/python3
# Copyright 2024 Standard Robots Co. All rights reserved.
import unittest

from protocol_adapter.huawei_model.base_task import BaseTask
from protocol_adapter.models.task import TaskType


class BaseTaskTest(unittest.TestCase):
    def test___str__(self):
        task = BaseTask(TaskType.Linear_Move_After_Raise_Shelf)
        self.assertTrue(hex(TaskType.Linear_Move_After_Raise_Shelf) in str(task))


if __name__ == '__main__':
    unittest.main()
