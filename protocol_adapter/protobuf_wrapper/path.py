#!/usr/bin/env python3

import math
from enum import IntEnum

from protocol_adapter.utils import AngleUtils


class Direction(IntEnum):
    Forward = 1
    BackForward = 2
    PathLeft = 3
    PathRight = 4
    SHELF_LEG_IDENTIFY = 0x21  # 货架腿识别


class PathType(IntEnum):
    PATH_ZERO = 0
    PATH_LINE = 1
    PATH_CIRCLE = 2
    PATH_BEZIER = 3
    PATH_ROTATE = 4


class Path:
    def __init__(self):
        # 距离单位均为mm
        self.type = PathType.PATH_ZERO

        self.sx = 0  # 起点
        self.sy = 0

        self.cx = 0
        self.cy = 0

        self.dx = 0
        self.dy = 0

        self.ex = 0  # 终点
        self.ey = 0

        self.rotate_angle = 0  # 角度单位为1/1000 rad
        self.radius = 0
        self.direction = Direction.Forward  # 0x01->前进；0x02->后退

        self.limit_v = 0  # 速度限制
        self.limit_w = 0

        self.req_lock_space = False  # 旋转路径时是否需要申请

    @staticmethod
    def create_line_path(sx, sy, ex, ey, direction=Direction.Forward, limit_v=0):
        path = Path()
        path.type = PathType.PATH_LINE
        path.sx = sx
        path.sy = sy
        path.ex = ex
        path.ey = ey
        path.direction = direction

        # 后退路径限制0.2m/s
        if direction == Direction.BackForward and path.limit_v > 200:
            path.limit_v = 200

        path.limit_v = limit_v
        return path

    @staticmethod
    def create_bezier_path(sx, sy, cx, cy, dx, dy, ex, ey, direction=Direction.Forward, limit_v=0):
        path = Path()
        path.type = PathType.PATH_BEZIER
        path.sx = sx
        path.sy = sy
        path.ex = ex
        path.ey = ey
        path.cx = cx
        path.cy = cy
        path.dx = dx
        path.dy = dy
        path.limit_v = limit_v
        path.direction = direction
        return path

    @staticmethod
    def create_circle_path(sx, sy, ex, ey, cx, cy, radius, direction=Direction.Forward, limit_v=0):
        path = Path()
        path.type = PathType.PATH_CIRCLE
        path.sx = sx
        path.sy = sy
        path.ex = ex
        path.ey = ey
        path.cx = cx
        path.cy = cy
        path.limit_v = limit_v
        path.radius = radius
        path.direction = direction
        return path

    @staticmethod
    def create_rotate_path(rotate_angle, limit_w=0, lock_space=False):
        path = Path()
        path.type = PathType.PATH_ROTATE
        path.rotate_angle = rotate_angle

        # 当前旋转路径设置角速度并不生效, src不支持
        path.limit_w = int((math.pi / 4) * 500)
        path.req_lock_space = lock_space
        return path

    def is_inner_point(self, x, y):
        det_x_s = x - self.sx
        det_y_s = y - self.sy
        det_x_e = x - self.ex
        det_y_e = y - self.ey
        return (
            det_x_s * det_y_e == det_x_e * det_y_s
            and det_x_s * det_x_e <= 0
            and det_y_s * det_y_e <= 0
        )

    def is_point_on_the_extending_line(self, x, y):
        """座标是否在当前路径方向的延长线上"""
        if self.type != PathType.PATH_LINE:
            return False

        det_x_s = x - self.sx
        det_y_s = y - self.sy
        det_x_e = x - self.ex
        det_y_e = y - self.ey

        det_x_se = self.ex - self.sx
        det_y_se = self.ey - self.sy

        # 共线(叉乘=0), 线外(点积>0), 且在路径方向的延长线上
        return (
            det_x_s * det_y_e == det_x_e * det_y_s
            and det_x_s * det_x_e + det_y_s * det_y_e > 0
            and det_x_s * det_x_se + det_y_s * det_y_se > 0
        )

    def begin_facing(self, ignore_direction: bool = False) -> float:
        """获取起始朝向，返回角度"""
        if self.type == PathType.PATH_LINE:
            facing = math.degrees(math.atan2(self.ey - self.sy, self.ex - self.sx))
        elif self.type in (PathType.PATH_CIRCLE, PathType.PATH_BEZIER):
            facing = math.degrees(math.atan2(self.cy - self.sy, self.cx - self.sx))
        elif self.type == PathType.PATH_ROTATE:
            # 旋转应该没有起始朝向，此处也返回末端朝向
            facing = math.degrees(self.rotate_angle / 1000)
        else:
            raise AssertionError(f'Invalid path type: {self.type}')

        if not ignore_direction:
            facing = self.get_face_angle_with_respect_to_direction(facing)
        return AngleUtils.normalize_360(facing)

    def end_facing(self, ignore_direction: bool = False) -> float:
        """获取末端朝向，返回角度"""
        if self.type == PathType.PATH_LINE:
            facing = math.degrees(math.atan2(self.ey - self.sy, self.ex - self.sx))
        elif self.type == PathType.PATH_CIRCLE:
            facing = math.degrees(math.atan2(self.ey - self.cy, self.ex - self.cx))
        elif self.type == PathType.PATH_BEZIER:
            facing = math.degrees(math.atan2(self.ey - self.dy, self.ex - self.dx))
        elif self.type == PathType.PATH_ROTATE:
            facing = math.degrees(self.rotate_angle / 1000)
        else:
            raise AssertionError(f'Invalid path type: {self.type}')

        if not ignore_direction:
            facing = self.get_face_angle_with_respect_to_direction(facing)
        return AngleUtils.normalize_360(facing)

    def get_face_angle_with_respect_to_direction(self, face_angle):
        if self.direction == Direction.BackForward:
            face_angle += 180
        elif self.direction == Direction.PathLeft:
            face_angle += 90
        elif self.direction == Direction.PathRight:
            face_angle -= 90
        return face_angle

    def update_direction_by_start_angle(self, start_angle):
        path_deg = self.begin_facing(ignore_direction=True)
        # 计算全向移动方向
        path_direction = Direction.Forward
        if AngleUtils.equal_norm(path_deg, AngleUtils.normalize_360(start_angle + 90), 5):
            path_direction = Direction.PathRight
        elif AngleUtils.equal_norm(path_deg, AngleUtils.normalize_360(start_angle - 90), 5):
            path_direction = Direction.PathLeft
        elif AngleUtils.equal_norm(path_deg, AngleUtils.normalize_360(start_angle + 180), 5):
            path_direction = Direction.BackForward
        self.direction = path_direction

    @property
    def length(self):
        if self.type in (PathType.PATH_LINE, PathType.PATH_BEZIER, PathType.PATH_CIRCLE):
            return math.dist([self.sx, self.sy], [self.ex, self.ey])
        else:
            return 0

    def __str__(self):
        if self.type == PathType.PATH_LINE:
            return (
                f'Line s({self.sx}, {self.sy}) e({self.ex}, {self.ey}) '
                f'dir:{self.direction}, {self.begin_facing(ignore_direction=True):.1f}°, len:{self.length / 1000:.3f}m, '
                f'v:{self.limit_v}'
            )
        elif self.type == PathType.PATH_CIRCLE:
            return (
                f'Circle s({self.sx}, {self.sy}) c({self.cx}, {self.cy}) e({self.ex}, {self.ey}) '
                f'dir:{self.direction}, {self.begin_facing(ignore_direction=True):.1f}--{self.end_facing(ignore_direction=True):.1f}°, '
                f'len:{self.length / 1000:.3f}m, v:{self.limit_v}'
            )
        elif self.type == PathType.PATH_BEZIER:
            return (
                f'Bezier s({self.sx}, {self.sy}) '
                f'c({self.cx}, {self.cy}) d({self.dx}, {self.dy}) e({self.ex}, {self.ey}) '
                f'dir:{self.direction}, {self.begin_facing(ignore_direction=True):.1f}_{self.end_facing(ignore_direction=True):.1f}°, '
                f'len:{self.length / 1000:.3f}m, v:{self.limit_v}, '
                f'dx:{abs(self.sx - self.ex) / 1000:.3f}m, dy:{abs(self.sy - self.ey) / 1000:.3f}m'
            )
        elif self.type == PathType.PATH_ROTATE:
            return f'Rotate {math.degrees(self.rotate_angle) / 1000:.1f}°'
        else:
            return f'Error path type: {self.type}!'

    def __repr__(self):
        return f'<{self.__str__()}>'


if __name__ == '__main__':
    path = Path.create_line_path(0, 0, 1000, 1040)
    print(path)
