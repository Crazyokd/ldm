#!/usr/bin/python3

import unittest

from protocol_adapter.models.task import TaskType
from protocol_adapter.huawei_model.linear_move_task import LinearMoveTask
from protocol_adapter.huawei_model.const import (
    RAISE_SHELF_MAX_PATH_LENGTH_THRESHOLD,
    RAISE_SHELF_MIN_PATH_LENGTH_THRESHOLD,
)


class LinearMoveTaskTest(unittest.TestCase):
    def test_calc_adjust_line_path(self):
        task = LinearMoveTask(TaskType.Linear_Move_After_Raise_Shelf)

        # 默认目标点(0, 0, 0)，计算当前座标到目标点的路径
        # 座标单位： (X mm, Y mm, D deg*1000)

        # 应该调整路径：目标点距离范围(闭区间):
        #   [RAISE_SHELF_MIN_PATH_LENGTH_THRESHOLD, RAISE_SHELF_MAX_PATH_LENGTH_THRESHOLD]
        self.assertTrue(
            RAISE_SHELF_MAX_PATH_LENGTH_THRESHOLD > RAISE_SHELF_MIN_PATH_LENGTH_THRESHOLD
        )
        self.assertTrue(RAISE_SHELF_MIN_PATH_LENGTH_THRESHOLD > 1)

        ANGLE_LIST = (0, 20, 1000, 90000, 180000, 200000)

        for angle in ANGLE_LIST:
            cur_pos = {'x': 0, 'y': 0, 'angle': angle}
            path = task.calculate_adjust_line_path(cur_pos)
            self.assertEqual(len(path), 0)

            cur_pos = {'x': 1, 'y': RAISE_SHELF_MIN_PATH_LENGTH_THRESHOLD - 1, 'angle': angle}
            path = task.calculate_adjust_line_path(cur_pos)
            self.assertEqual(len(path), 0)

            cur_pos = {'x': 1, 'y': RAISE_SHELF_MAX_PATH_LENGTH_THRESHOLD, 'angle': angle}
            path = task.calculate_adjust_line_path(cur_pos)
            self.assertEqual(len(path), 0)

            cur_pos = {'x': 0, 'y': RAISE_SHELF_MIN_PATH_LENGTH_THRESHOLD, 'angle': angle}
            path = task.calculate_adjust_line_path(cur_pos)
            self.assertEqual(len(path), 1)

            cur_pos = {'x': RAISE_SHELF_MIN_PATH_LENGTH_THRESHOLD, 'y': 0, 'angle': angle}
            path = task.calculate_adjust_line_path(cur_pos)
            self.assertEqual(len(path), 1)

            cur_pos = {'x': 0, 'y': RAISE_SHELF_MAX_PATH_LENGTH_THRESHOLD, 'angle': angle}
            path = task.calculate_adjust_line_path(cur_pos)
            self.assertEqual(len(path), 1)


if __name__ == '__main__':
    unittest.main()
