import logging

from protocol_adapter.huawei_model.base import Base
from protocol_adapter.huawei_model.const import get_int_dat, TargetType

_logger = logging.getLogger(__name__)


class MoveTarget(Base):
    def __init__(self):
        self.x = 0  # x坐标，单位mm
        self.y = 0
        self.angle = 0  # 方向, 单位1/1000 degree
        self.target_type = TargetType.Normal
        self.task_precision = 0  # 任务精度等级
        self.target_precision = 0  # 距离精度等级, 单位mm
        self.angle_precision = 0  # 小车角度精度要求, 单位1/1000 degree
        self.shelf_angle_precision = 0  # 货架角度精度要求, 单位1/1000 degree
        self.limit_max_speed = 1000  # 最大速度限制
        self.move_direction = 0  # 全向车移动方向，单位单位1/1000 degree
        self.final_x = 0  # 最终目标信息
        self.final_y = 0
        self.reserved = 0

    def from_dat(self, dat):
        if len(dat) < 60:
            _logger.error(f'Invalid move target dat length {len(dat)}')
            return
        self.x = get_int_dat(dat, 0, 4)
        self.y = get_int_dat(dat, 4, 4)
        self.angle = get_int_dat(dat, 8, 4)
        self.target_type = get_int_dat(dat, 12, 1)
        self.task_precision = get_int_dat(dat, 13, 1)
        self.target_precision = get_int_dat(dat, 14, 2, signed=False)
        self.angle_precision = get_int_dat(dat, 16, 4, signed=False)
        self.shelf_angle_precision = get_int_dat(dat, 20, 4, signed=False)
        self.limit_max_speed = get_int_dat(dat, 24, 4)
        self.move_direction = get_int_dat(dat, 28, 4)
        self.final_x = get_int_dat(dat, 52, 4)
        self.final_y = get_int_dat(dat, 56, 4)

    def get_target(self):
        return {'x': self.x, 'y': self.y, 'angle': self.angle}

    def get_limit_v(self):
        return self.limit_max_speed

    def __str__(self):
        return (
            f'target({self.x}, {self.y}, {self.angle})'
            f'{{direction:{self.move_direction},limit:{self.limit_max_speed}}} '
        )
