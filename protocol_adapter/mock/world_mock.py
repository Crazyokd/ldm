#!/usr/bin/python3
# Copyright 2024 Standard Robots Co. All rights reserved.
# 若没特殊说明，单位统一用角度和米
import math
import logging
from typing import Tuple

from protocol_adapter.utils import MiscUtils
from protocol_adapter.protobuf_wrapper.base import Point, Pose

_logger = logging.getLogger(__name__)


@MiscUtils.singleton
class WorldMock:
    def __init__(self):
        self.reset()

    def reset(self):
        self._shelf_id: str = ''
        self._shelf_pose = Pose()
        self._charging_station_pose = Pose()

        self.charging_station_positions = []
        self.shelf_positions = {}
        self.init_pose = {}

    def load_mock_positions(self, data: dict):
        if data.get('charge_station'):
            self.charging_station_positions = [Pose(*pos) for pos in data['charge_station']]

        if data.get('shelf'):
            self.shelf_positions = data['shelf'].copy()

            for shelf_id, pos in self.shelf_positions.items():
                self.shelf_positions[shelf_id] = Pose(*pos)

        if data.get('init_pose'):
            self.init_pose = data['init_pose'].copy()

    def set_charging_station_pose(self, pose: Pose):
        self._charging_station_pose = pose

    def get_charging_station_pose(self) -> Pose:
        return self._charging_station_pose

    def is_get_charging_station(self, pose: Pose) -> bool:
        """是否能够到充电桩"""
        DISTANCE_ACCEPT_DIFF = 1  # 可接受的两个认为同一个位置的距离
        ANGLE_ACCEPT_DIFF = 10  # 可接受的角度偏差
        for station_pose in [self._charging_station_pose] + self.charging_station_positions:
            if station_pose is None:
                continue
            if (
                station_pose.distance(pose) < DISTANCE_ACCEPT_DIFF
                and station_pose.angle_diff(pose) < ANGLE_ACCEPT_DIFF
            ):
                return True
        return False

    def set_shelf(self, shelf_id: str, pose: Pose):
        """测试时，第一次设置货架位置"""
        self._shelf_id = shelf_id
        self._shelf_pose = pose

    def set_shelf_point(self, shelf_id: str, point: Point):
        """开启顶升旋转时，只变更位置，不变更角度"""
        assert self._shelf_id == shelf_id
        self._shelf_pose.set_point(point)

    def set_shelf_angle(self, shelf_id: str, angle: float):
        """(4, 12, x)时，只变更角度，不变更位置"""
        assert self._shelf_id == shelf_id
        self._shelf_pose.yaw = angle

    def get_shelf(self, pose: Pose) -> str:
        """用于测试时，断言货架的位置"""
        DISTANCE_ACCEPT_DIFF = 1  # 可接受的两个认为同一个位置的距离
        ANGLE_ACCEPT_DIFF = 10  # 可接受的角度偏差

        shelf_dict: dict = self.shelf_positions.copy()
        if self._shelf_id:
            shelf_dict[self._shelf_id] = self._shelf_pose

        for shelf_id, shelf_pose in shelf_dict.items():
            if shelf_id and (
                shelf_pose.distance(pose) < DISTANCE_ACCEPT_DIFF
                and shelf_pose.angle_diff(pose) < ANGLE_ACCEPT_DIFF
            ):
                return shelf_id

        _logger.error('该位置附近未找到货架信息')
        return ''

    def get_shelf_by_point(self, point: Point) -> Tuple[str, Pose]:
        """顶升时，扫码时，车辆只知道货架的大概位置，实际位置和角度值都需要根据实际摆放位置返回"""
        DISTANCE_ACCEPT_DIFF = 1  # 可接受的两个认为同一个位置的距离

        shelf_dict: dict = self.shelf_positions.copy()
        if self._shelf_id:
            shelf_dict[self._shelf_id] = self._shelf_pose

        for shelf_id, shelf_pose in shelf_dict.items():
            if shelf_id and math.dist(shelf_pose.point(), point) < DISTANCE_ACCEPT_DIFF:
                return shelf_id, shelf_pose

        _logger.error('该位置附近未找到货架信息')
        return '', Pose()


if __name__ == '__main__':
    world1 = WorldMock()
    charging_station_pose = Pose(1, 2, 30)
    print(charging_station_pose)
    world1.set_charging_station_pose(charging_station_pose)
    world2 = WorldMock()
    pose = world2.get_charging_station_pose()
    print(pose.x, pose.y, pose.yaw)  # 1 2 30
    print(world1 is world2)  # True
