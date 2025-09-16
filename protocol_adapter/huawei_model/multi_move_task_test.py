#!/usr/bin/python3

import unittest
import copy
import math
import random

from protocol_adapter.models.task import TaskType
from protocol_adapter.huawei_model.const import (
    SHELF_ROTATE_ANGLE_THRESHOLD,
    MAX_POSITION_DEVIATION_FOR_NET_REGRESSION_MM,
)
from protocol_adapter.huawei_model.point import SimplePoint
from protocol_adapter.huawei_model.multi_move_task import MultiMoveTask
from protocol_adapter.huawei_model.move_target import MoveTarget
from protocol_adapter.huawei_model.bezier import verify_curvature_is_robot_acceptable
from protocol_adapter.huawei_model.utils_plot import path_to_cubic_bezier
from protocol_adapter.protobuf_wrapper.path import PathType
from protocol_adapter.utils import AngleUtils


class MultiMoveTaskTest(unittest.TestCase):
    def test_redo_finish_task(self):
        """任务结束后，走到了路径的终点，继续重新执行此次任务，不允许回起点"""
        task = MultiMoveTask(TaskType.Multi_Path_No_Payload_Move)
        p1 = [
            SimplePoint(116472, 133554, 1),
            SimplePoint(116472, 134518, 1),
            SimplePoint(116472, 135482, 1),
            SimplePoint(115788, 135482, 1),
            SimplePoint(115446, 135482, 1),
            SimplePoint(115104, 135482, 1),
        ]
        p2 = [
            SimplePoint(115104, 135482, 0),
            SimplePoint(110974, 135482, 0),
        ]
        task.path_points_groups.append(p1)
        task.path_points_groups.append(p2)
        task.move_target = MoveTarget()
        task.move_target.x = 110974
        task.move_target.y = 135482
        task.move_target.angle = 180000

        paths = task.calculate_move_path({'x': 110971, 'y': 135486, 'angle': 180000}, True)
        self.assertEqual(len(paths), 0, '生成路径有问题，回起点了？')

    def test_robot_path_overreach(self):
        """当机器人距离规划路径过远时，不能执行当前任务"""
        task = MultiMoveTask(TaskType.Multi_Path_No_Payload_Move)
        p1 = [
            SimplePoint(116472, 133554, 1),
            SimplePoint(116472, 134518, 1),
            SimplePoint(116472, 135482, 1),
            SimplePoint(115788, 135482, 1),
            SimplePoint(115446, 135482, 1),
            SimplePoint(115104, 135482, 1),
        ]
        p2 = [
            SimplePoint(115104, 135482, 0),
            SimplePoint(110974, 135482, 0),
        ]
        task.path_points_groups.append(p1)
        task.path_points_groups.append(p2)
        task.move_target = MoveTarget()
        task.move_target.x = 110974
        task.move_target.y = 135482
        task.move_target.angle = 180000

        paths = task.calculate_move_path(
            {'x': 110971 + 10 * 1000, 'y': 135486, 'angle': 180000}, True
        )
        self.assertEqual(len(paths), 0, f'生成路径有问题，回起点了？')

    def test_origin_short_path_regression(self):
        """起始路径短距离回归测试。
        期望机器人距离路网很近时，直接生成去第一条路的终点，而不是旋转到第一条路的起点，这样规避了不必要的旋转
        """
        task = MultiMoveTask(TaskType.Multi_Path_No_Payload_Move)
        p1 = [
            SimplePoint(0, 0, 0),
            SimplePoint(2000, 0, 0),
        ]
        p2 = [
            SimplePoint(2000, 0, 1),
            SimplePoint(3000, 3500, 1),
            SimplePoint(4000, 4000, 1),
        ]
        task.path_points_groups.append(p1)
        task.path_points_groups.append(p2)
        task.move_target = MoveTarget()
        task.move_target.x = 4000
        task.move_target.y = 4000
        task.move_target.angle = 90000

        test_start_points = [
            {'x': 0, 'y': 0, 'angle': 0},
            {'x': 40, 'y': 0, 'angle': 0},
            {'x': -40, 'y': 0, 'angle': 0},
            {'x': 0, 'y': 40, 'angle': 0},
            {'x': 0, 'y': -40, 'angle': 0},
            {'x': 20, 'y': 20, 'angle': 0},
            {'x': 20, 'y': -20, 'angle': 0},
            {'x': -20, 'y': 20, 'angle': 0},
            {'x': -20, 'y': -20, 'angle': 0},
            {'x': -100, 'y': -20, 'angle': 0},
            {'x': -100, 'y': 20, 'angle': 0},
        ]
        for start_point in test_start_points:
            tmp_task = copy.deepcopy(task)  # 路径可能会被删除，所以每次要用新的
            paths = tmp_task.calculate_move_path(start_point, need_check_start_pose=True)
            self.assertGreater(len(paths), 0)
            self.assertAlmostEqual(paths[0].sx, start_point['x'], delta=10)
            self.assertAlmostEqual(paths[0].sy, start_point['y'], delta=10)
            self.assertAlmostEqual(paths[0].ex, p1[1].x, delta=10)
            self.assertAlmostEqual(paths[0].ey, p1[1].y, delta=10)

    def test_find_near_path(self):
        """测试车在最近路网附近策略"""
        task = MultiMoveTask(TaskType.Multi_Path_No_Payload_Move)
        p1 = [
            SimplePoint(111820, 109860, 0),
            SimplePoint(111740, 109860, 0),
        ]
        p2 = [
            SimplePoint(111740, 109860, 0),
            SimplePoint(110295, 109860, 0),
        ]
        p3 = [
            SimplePoint(110295, 109860, 1),
            SimplePoint(110056, 109860, 1),
            SimplePoint(109816, 109860, 1),
            SimplePoint(109337, 109860, 1),
            SimplePoint(109337, 110875, 1),
        ]
        task.path_points_groups.append(p1)
        task.path_points_groups.append(p2)
        task.path_points_groups.append(p3)
        task.move_target = MoveTarget()
        task.move_target.x = 4000
        task.move_target.y = 4000
        task.move_target.angle = 90000

        start_point = {'x': 111819, 'y': 109845, 'angle': 180000}
        paths = task.calculate_move_path(start_point, need_check_start_pose=True)
        self.assertEqual(len(paths), 2, '车辆应该认为它自己在第二条路径上，不然容易形成很多旋转')

    def test_bezier_fitting(self):
        """测试贝塞尔曲线拟合"""
        # 要测试的路网数据
        paths_to_test = [
            # 不容易出错的情况
            {
                'start_point': {'x': 109376, 'y': 122770, 'angle': 97001},
                'path_points_groups': [
                    [
                        SimplePoint(110295, 121910, 1),
                        SimplePoint(110056, 121910, 1),
                        SimplePoint(109816, 121910, 1),
                        SimplePoint(109337, 121910, 1),
                        SimplePoint(109337, 122891, 1),
                        SimplePoint(109337, 123871, 1),
                    ]
                ],
            },
            {
                'start_point': {'x': 122001, 'y': 54328, 'angle': -89897},
                'path_points_groups': [
                    [
                        SimplePoint(121990, 54329, 1),
                        SimplePoint(121990, 53040, 1),
                        SimplePoint(121990, 51750, 1),
                        SimplePoint(121365, 51750, 1),
                        SimplePoint(121053, 51750, 1),
                        SimplePoint(120740, 51750, 1),
                    ]
                ],
            },
            # 容易出错的情况
            {
                'start_point': {'x': 117918, 'y': 127522, 'angle': 178098},
                'path_points_groups': [
                    [
                        SimplePoint(117897, 127643, 1),
                        SimplePoint(117541, 127643, 1),
                        SimplePoint(117185, 127643, 1),
                        SimplePoint(116472, 127643, 1),
                        SimplePoint(116472, 127991, 1),
                        SimplePoint(116472, 128338, 1),
                    ]
                ],
            },
            {
                'start_point': {'x': 48067, 'y': 199815, 'angle': -91157},
                'path_points_groups': [
                    [
                        SimplePoint(48600, 203847, 1),
                        SimplePoint(48600, 202706, 1),
                        SimplePoint(48600, 201566, 1),
                        SimplePoint(48066, 201566, 1),
                        SimplePoint(48066, 200425, 1),
                        SimplePoint(48066, 199284, 1),
                    ]
                ],
            },
        ]
        # 起点用一组随机数
        for _ in range(10):
            # 约束下，不能偏差超过200mm
            for _ in range(100):
                x_error = random.randint(-200, 200)
                y_error = random.randint(-200, 200)
                if x_error**2 + y_error**2 < 200**2:
                    break
            else:
                break
            paths_to_test.append(
                {
                    'start_point': {
                        'x': 117897 + x_error,
                        'y': 127643 + y_error,
                        'angle': 180000 + random.randint(-10000, 10000),
                    },
                    'path_points_groups': [
                        [
                            SimplePoint(117897, 127643, 1),
                            SimplePoint(117541, 127643, 1),
                            SimplePoint(117185, 127643, 1),
                            SimplePoint(116472, 127643, 1),
                            SimplePoint(116472, 127991, 1),
                            SimplePoint(116472, 128338, 1),
                        ]
                    ],
                }
            )

        for data_to_test_index, path_to_test in enumerate(paths_to_test):
            task = MultiMoveTask(TaskType.Multi_Path_No_Payload_Move)
            task.path_points_groups = path_to_test['path_points_groups']
            paths = task.calculate_move_path(
                path_to_test['start_point'], need_check_start_pose=True
            )
            self.assertNotEqual(paths, 0, '未生成路径')
            for path_of_index, path in enumerate(paths):
                if path.type != PathType.PATH_BEZIER:
                    continue
                bezier = path_to_cubic_bezier(path)
                # 曲率判断
                is_robot_acceptable, t, curvature = verify_curvature_is_robot_acceptable(bezier)
                self.assertTrue(
                    is_robot_acceptable,
                    f'第{data_to_test_index}组测试数据生成的第{path_of_index}在t={t}处曲率过大,'
                    f'{curvature},起点{path_to_test["start_point"]}',
                )
                # 判断生成的曲线与下发的曲线偏差
                for i in range(100):
                    t = i / 100.0
                    p = bezier.curve(t)
                    start_point = {'x': p[0] * 1000, 'y': p[1] * 1000}
                    task = MultiMoveTask(TaskType.Multi_Path_No_Payload_Move)
                    task.path_points_groups = path_to_test['path_points_groups']
                    min_t, min_idex = task.find_near_path(
                        start_point, MAX_POSITION_DEVIATION_FOR_NET_REGRESSION_MM
                    )
                    self.assertNotEqual(
                        -1,
                        min_idex,
                        f'第{data_to_test_index}组测试数据生成的第{path_of_index}在t={t}处位置偏差过大,'
                        f'测试点{start_point}',
                    )

    def test_almost_at_dst_pose(self):
        """当车辆几乎接近目标点时，不应该规划路径，很短的路径会有各种旋转，
        而且由于定位误差和控制误差，很短的路径也走不准"""
        task = MultiMoveTask(TaskType.Multi_Path_No_Payload_Move)
        p1 = [
            SimplePoint(94366, 151420, 1),
            SimplePoint(94778, 151420, 1),
            SimplePoint(95190, 151420, 1),
            SimplePoint(96013, 151420, 1),
            SimplePoint(96013, 150638, 1),
            SimplePoint(96013, 149855, 1),
        ]
        task.path_points_groups.append(p1)
        task.move_target = MoveTarget()
        task.move_target.x = 96013
        task.move_target.y = 149855
        task.move_target.angle = -90000

        paths = task.calculate_move_path({'x': 96027, 'y': 149872, 'angle': -90068}, True)
        self.assertEqual(len(paths), 0)

    def test_singular_matrix_exception(self):
        """测试numpy抛numpy.linalg.LinAlgError: Singular matrix的异常,也是距离目标点过近导致"""
        task = MultiMoveTask(TaskType.Multi_Path_No_Payload_Move)
        p1 = [
            SimplePoint(100076, 133484, 1, 300),
            SimplePoint(100076, 134483, 1, 300),
            SimplePoint(100076, 135482, 1, 300),
            SimplePoint(100439, 135482, 1, 300),
            SimplePoint(100621, 135482, 1, 300),
            SimplePoint(100802, 135482, 1, 300),
        ]
        # 注释掉画图
        # b5 = simple_points_to_quintic_bezier(p1)
        # b5.plot_curve_and_curvature()
        task.path_points_groups.append(p1)
        task.move_target = MoveTarget()
        task.move_target.x = 100802
        task.move_target.y = 135482
        task.move_target.angle = 0

        paths = task.calculate_move_path({'x': 100805, 'y': 135496, 'angle': 5042}, True)
        for path in paths:
            # 注释掉画图
            # if path.type == PathType.PATH_BEZIER:
            #     b3 = path_to_cubic_bezier(path)
            #     b3.plot_curve_and_curvature()
            print(path)

    def test_bezier_fitting_near_the_end(self):
        """车在贝塞尔末端附近，容易拟合出有很大角度转动的贝塞尔"""
        task = MultiMoveTask(TaskType.Multi_Path_No_Payload_Move)
        p1 = [
            SimplePoint(46340, 301084, 1, 300),
            SimplePoint(46735, 301084, 1, 300),
            SimplePoint(47130, 301084, 1, 300),
            SimplePoint(47920, 301084, 1, 300),
            SimplePoint(47920, 300313, 1, 300),
            SimplePoint(47920, 299541, 1, 300),
        ]
        p2 = [SimplePoint(47920, 299541, 0, 300), SimplePoint(47920, 293410, 0, 300)]

        task.path_points_groups.append(p1)
        task.path_points_groups.append(p2)
        task.move_target = MoveTarget()
        task.move_target.x = 47920
        task.move_target.y = 293410
        task.move_target.angle = -90000

        curr_pose = {'x': 48039, 'y': 299901, 'angle': -90871}
        paths = task.calculate_move_path(curr_pose, True)
        self.assertEqual(paths[0].type, PathType.PATH_ROTATE)
        diff = AngleUtils.delta_norm(
            curr_pose['angle'] / 1000, math.degrees(paths[0].rotate_angle / 1000)
        )
        self.assertLessEqual(diff, SHELF_ROTATE_ANGLE_THRESHOLD)


if __name__ == '__main__':
    unittest.main()
