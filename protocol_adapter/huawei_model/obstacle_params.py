import logging

from protocol_adapter.huawei_model.const import get_int_dat
from protocol_adapter.huawei_model.base import Base

_logger = logging.getLogger(__name__)

BYTE_NUM_SLOWDOWN_AREA = 24


class SlowDownArea(Base):
    def __init__(self):
        self.forward = 0  # 前向距离, 2字节
        self.backward = 0
        self.left = 0
        self.right = 0
        self.speed = 0  # 速度, 4字节
        self.dec_speed = 0  # 减速度，4字节

    def from_dat(self, dat):
        if len(dat) < 24:
            _logger.error('Invalid slow down area')
        self.forward = get_int_dat(dat, 0, 2)
        self.backward = get_int_dat(dat, 2, 2)
        self.left = get_int_dat(dat, 4, 2)
        self.right = get_int_dat(dat, 6, 2)
        self.speed = get_int_dat(dat, 8, 4)
        self.dec_speed = get_int_dat(dat, 12, 4)

    def get_oba_params(self):
        return self.forward, self.backward, self.left, self.right


class ObstacleParams(Base):
    def __init__(self):
        self.distance_threshold = 0  # 距离阈值
        self.index_key = 0  # 功能索引
        self.stop_forward = 0  # 停止区
        self.stop_back = 0
        self.stop_left = 0
        self.stop_right = 0

        self.slowdown_areas = None
        self.user_defined = 0
        self.reserved = 0

    def from_dat(self, dat):
        if len(dat) < 72:
            _logger.error('Invalid oba data length')
            return
        self.distance_threshold = get_int_dat(dat, 0, 2)
        self.index_key = dat[3]
        self.stop_forward = get_int_dat(dat, 4, 2)
        self.stop_back = get_int_dat(dat, 6, 2)
        self.stop_left = get_int_dat(dat, 8, 2)
        self.stop_right = get_int_dat(dat, 10, 2)

        cur_index = 12
        self.slowdown_areas = []
        if self.index_key == 0:
            for _ in range(0, 2):
                area_dat = dat[cur_index : cur_index + BYTE_NUM_SLOWDOWN_AREA]
                area = SlowDownArea()
                area.from_dat(area_dat)
                self.slowdown_areas.append(area)
                cur_index += BYTE_NUM_SLOWDOWN_AREA

        self.user_defined = get_int_dat(dat, 60, 8)
        self.reserved = get_int_dat(dat, 68, 4)

    # 是否由服务器控制避障策略
    def is_enable_server_ctrl_oba_policy(self):
        return self.distance_threshold != 0

    # 前、后、左、右
    def get_oba_stop_params(self):
        return self.stop_forward, self.stop_back, self.stop_left, self.stop_right

    # 前、后、左、右
    def get_oba_slow_params(self):
        if not self.slowdown_areas:
            return 0, 0, 0, 0
        return self.slowdown_areas[0].get_oba_params()

    def __str__(self):
        result = f'obsParam: [{super().__str__()}]'
        if self.slowdown_areas:
            result += '\n  slow areas:[{}]'.format(','.join(f'[{x}]' for x in self.slowdown_areas))
        return result
