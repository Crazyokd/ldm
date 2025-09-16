import unittest

from protocol_adapter.huawei_model.point import SimplePoint
from protocol_adapter.huawei_model.utils_plot import transform_by_rotate_scale_and_move


class UtilsPlotTest(unittest.TestCase):
    def test_transform_by_rotate_scale_and_move(self):
        p0 = [
            SimplePoint(0, 20, 0),
            SimplePoint(12, 2, 1, 40),
        ]

        p1 = transform_by_rotate_scale_and_move(
            p0,
            rotate_deg=90,
            scale=1,
            ref_point=SimplePoint(),
            ref_point_after=SimplePoint(),
        )

        self.assertAlmostEqual(p1[0].x, -20, delta=1e-6)
        self.assertAlmostEqual(p1[0].y, 0, delta=1e-6)
        self.assertEqual(p1[0].point_type, 0)

        self.assertAlmostEqual(p1[1].x, -2, delta=1e-6)
        self.assertAlmostEqual(p1[1].y, 12, delta=1e-6)
        self.assertEqual(p1[1].point_type, 1)
        self.assertEqual(p1[1].limit_v, 40)

        p2 = transform_by_rotate_scale_and_move(
            p0,
            rotate_deg=0,
            scale=0.5,
            ref_point=p0[0],
            ref_point_after=SimplePoint(),
        )

        self.assertAlmostEqual(p2[0].x, 0, delta=1e-6)
        self.assertAlmostEqual(p2[0].y, 0, delta=1e-6)
        self.assertEqual(p2[0].point_type, 0)

        self.assertAlmostEqual(p2[1].x, 6, delta=1e-6)
        self.assertAlmostEqual(p2[1].y, -9, delta=1e-6)
        self.assertEqual(p2[1].point_type, 1)
        self.assertEqual(p2[1].limit_v, 40)
