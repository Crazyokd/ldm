# Copyright 2024 Standard Robots Co. All rights reserved.
import unittest
import numpy as np
from protocol_adapter.huawei_model.bezier import CubicBezier


class CubicBezierTest(unittest.TestCase):
    def test_derivative(self):
        bezier = CubicBezier([0, 0], [0, 1], [4, 1], [4, 0])
        self.assertAlmostEqual(bezier.derivative(0)[0], 0)
        self.assertAlmostEqual(bezier.derivative(0.5)[1], 0)
        self.assertAlmostEqual(bezier.derivative(1)[0], 0)

    def test_curvature(self):
        # 对于一条直线，曲率应该为 0
        bezier = CubicBezier([0, 0], [1, 1], [2, 2], [3, 3])
        for t in np.linspace(0, 1, 10):
            curvature = bezier.curvature(t)
            self.assertEqual(curvature, 0, f'Expected curvature to be 0 at t={t}')

        # 可以用肉眼观察下相对于半径为1的圆的曲率
        bezier = CubicBezier([1, 0], [1, 1.3], [-1, 1.3], [-1, 0])
        self.assertLess(bezier.curvature(0), 1)
        self.assertGreater(bezier.curvature(0.2), 1)
        self.assertLess(bezier.curvature(0.5), 1)
        self.assertGreater(bezier.curvature(0.8), 1)
        self.assertLess(bezier.curvature(1), 1)


if __name__ == '__main__':
    unittest.main()
