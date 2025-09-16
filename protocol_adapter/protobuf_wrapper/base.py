#!/usr/bin/python3
# Copyright 2024 Standard Robots Co. All rights reserved.
# 若没特殊说明，单位统一用角度和米
import math

from dataclasses import dataclass, fields

from protocol_adapter.utils import AngleUtils

DISTANCE_ACCEPT_DIFF = 0.1  # 可接受的两个认为同一个位置的距离


@dataclass
class Point:
    x: float = 0
    y: float = 0

    def is_same_point(self, other) -> bool:
        return math.dist(self, other) <= DISTANCE_ACCEPT_DIFF

    def __iter__(self):
        return (getattr(self, field.name) for field in fields(self))

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar):
        return Point(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar):
        return Point(self.x / scalar, self.y / scalar)


@dataclass
class Pose:
    x: float = 0
    y: float = 0
    yaw: float = 0

    def point(self) -> Point:
        return Point(self.x, self.y)

    def set_point(self, p: Point) -> None:
        self.x = p.x
        self.y = p.y

    def distance(self, other) -> float:
        return math.dist(self.point(), other.point())

    def angle_diff(self, other) -> float:
        return AngleUtils.delta_norm(self.yaw, other.yaw)


def rotate_to_target(src: float, dst: float, step: float) -> float:
    """从当前src角度，转到dst角度，每次最多转stp，可以正转也可以反转。返回这一次转到的角度"""
    dst = AngleUtils.normalize_360(dst)
    diff = AngleUtils.delta_norm(src, dst)
    if diff <= step:
        return dst

    tmp_target = src + step
    if AngleUtils.delta_norm(tmp_target, dst) < diff:
        return tmp_target

    return AngleUtils.normalize_360(src - step)
