import math

from .angle import AngleUtils


class GeometryUtils:
    @staticmethod
    def is_same_pose(p1, p2, *, threshold=300, threshold_angle=30, ignore_angle=False):
        # 单位: mm, mdeg
        if any((abs(p1['x'] - p2['x']) > threshold, abs(p1['y'] - p2['y']) > threshold)):
            return False
        return ignore_angle or AngleUtils.equal_norm(
            p1['angle'] / 1000, p2['angle'] / 1000, threshold=threshold_angle
        )

    @staticmethod
    def is_same_point(p1, p2, threshold=300, threshold_angle=30):
        if any((abs(p1.x - p2.x) > threshold, abs(p1.y - p2.y) > threshold)):
            return False
        return AngleUtils.equal_norm(p1.angle / 1000, p2.angle / 1000, threshold=threshold_angle)

    @staticmethod
    def calculate_distance(sx, sy, ex, ey):
        return math.sqrt((ex - sx) ** 2 + (ey - sy) ** 2)

    @staticmethod
    def calculate_circle(p1, p2, p3):
        a = p1['x'] - p2['x']
        b = p1['y'] - p2['y']
        c = p1['x'] - p3['x']
        d = p1['y'] - p3['y']
        e = ((p1['x'] ** 2 - p2['x'] ** 2) - (p2['y'] ** 2 - p1['y'] ** 2)) / 2
        f = ((p1['x'] ** 2 - p3['x'] ** 2) - (p3['y'] ** 2 - p1['y'] ** 2)) / 2
        cx = -(d * e - b * f) / (b * c - a * d)
        cy = -(a * f - c * e) / (b * c - a * d)
        r = math.sqrt((p1['x'] - cx) ** 2 + (p1['y'] - cy) ** 2)
        if (p2['x'] - p1['x']) * (p3['y'] - p2['y']) - (p2['y'] - p1['y']) * (
            p3['x'] - p2['x']
        ) < 0:
            r = -r
        return cx, cy, r

    @staticmethod
    def calculate_angle(sx, sy, ex, ey):
        """计算起始点方向的弧度值，[0, 2pi)"""
        rad = math.atan2(ey - sy, ex - sx)
        if rad < 0:
            rad += 2 * math.pi
        return rad
