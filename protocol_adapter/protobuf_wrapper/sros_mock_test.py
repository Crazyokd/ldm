#!/usr/bin/python3
# Copyright 2024 Standard Robots Co. All rights reserved.
import unittest
import math

from protocol_adapter.protobuf_wrapper.path import Path
from protocol_adapter.protobuf_wrapper.base import Point
from protocol_adapter.mock.sros_mock import (
    move_to_target_at_line,
    get_pose_from_bezier,
    move_to_target_at_bezier,
)


class SrosMockTest(unittest.TestCase):
    def test_point(self):
        src = Point()
        dst = Point(1, 1)
        self.assertEqual(math.dist(src, dst), math.sqrt(2))
        self.assertEqual(src + dst, dst)
        self.assertEqual(dst * 3, Point(3, 3))
        src_2 = Point(0.001, 0.0001)
        self.assertTrue(src.is_same_point(src_2))

    def test_move_to_target(self):
        # 测试一步是否走指定步长
        src = Point()
        path = Path.create_line_path(src.x, src.y, -1, -1)
        p = move_to_target_at_line(path, src, 1)
        self.assertAlmostEqual(math.dist(p, Point()), 1, delta=0.001)

        # 测试是否走到终点
        dst = Point(0, 1)
        path = Path.create_line_path(src.x, src.y, dst.x, dst.y)
        for _ in range(10):
            src = move_to_target_at_line(path, src, 0.2)
            if math.dist(dst, src) < 0.001:
                break
        self.assertAlmostEqual(math.dist(dst, src), 0, delta=0.001)

    def test_get_pose_from_bezier(self):
        path = Path.create_bezier_path(0, 0, 0, 1, 1, 1, 1, 0)
        p = get_pose_from_bezier(path, 0)
        self.assertAlmostEqual(p.x, 0, delta=0.001)
        self.assertAlmostEqual(p.y, 0, delta=0.001)
        self.assertAlmostEqual(p.yaw, 90, delta=0.001)
        p = get_pose_from_bezier(path, 0.5)
        self.assertAlmostEqual(p.x, 0.5, delta=0.001)
        self.assertAlmostEqual(p.y, 0.75, delta=0.001)
        self.assertAlmostEqual(p.yaw, 0, delta=0.001)
        p = get_pose_from_bezier(path, 1)
        self.assertAlmostEqual(p.x, 1, delta=0.001)
        self.assertAlmostEqual(p.y, 0, delta=0.001)
        self.assertAlmostEqual(p.yaw, 270, delta=0.001)

    def test_move_to_target_at_bezier(self):
        path = Path.create_bezier_path(0, 0, 0, 1, 1, 1, 1, 0)
        pose, t = move_to_target_at_bezier(path, 0, 10000)
        self.assertAlmostEqual(pose.x, 1, delta=0.001)
        self.assertAlmostEqual(pose.y, 0, delta=0.001)
        self.assertAlmostEqual(pose.yaw, 270, delta=0.001)
        self.assertAlmostEqual(t, 1, delta=0.001)


if __name__ == '__main__':
    unittest.main()
