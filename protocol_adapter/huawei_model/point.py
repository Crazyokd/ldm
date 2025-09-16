from protocol_adapter.huawei_model.base import Base
from protocol_adapter.huawei_model.const import get_int_dat, BYTES_ORDER
from protocol_adapter.utils import AngleUtils

SAME_POINT_XY_THRESHOLD = 5


class Point(Base):
    def __init__(self, x=0, y=0, angle=0, max_speed=1000):
        self.x = x  # 单位mm
        self.y = y
        self.angle = angle  # 单位1/1000角度
        self.max_speed = max_speed  # 单位mm/s

    def from_dat(self, dat):
        self.x = get_int_dat(dat, 0, 4)
        self.y = get_int_dat(dat, 4, 4)
        self.angle = get_int_dat(dat, 8, 4)
        self.max_speed = get_int_dat(dat, 12, 4)

    def to_dat(self):
        ba = bytearray()
        ba.extend(self.x.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(self.y.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
        ba.extend((self.angle).to_bytes(4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(self.max_speed.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
        return ba

    def is_equal(self, p):
        return (
            abs(self.x - p.x) <= SAME_POINT_XY_THRESHOLD
            and abs(self.y - p.y) <= SAME_POINT_XY_THRESHOLD
            and AngleUtils.equal_norm(self.angle, p.angle, 5)
        )

    def get_angle(self):
        return self.angle / 1000

    def get_max_speed(self):
        return self.max_speed

    def __str__(self):
        return f'({self.x}, {self.y}, {self.angle})'


# mm
class SimplePoint:
    def __init__(self, x=0, y=0, point_type=0, limit_v=1000):
        self.x = x
        self.y = y
        self.point_type = point_type
        self.limit_v = limit_v

    def from_dat(self, dat):
        self.x = get_int_dat(dat, 0, 4)
        self.y = get_int_dat(dat, 4, 4)

    def copy(self):
        ret = SimplePoint()
        ret.x = self.x
        ret.y = self.y
        ret.point_type = self.point_type
        return ret

    def __add__(self, other):
        ret = self.copy()
        if isinstance(other, SimplePoint):
            ret.x += other.x
            ret.y += other.y
        return ret

    def __sub__(self, other):
        ret = self.copy()
        if isinstance(other, SimplePoint):
            ret.x -= other.x
            ret.y -= other.y
        return ret

    def __mul__(self, k):
        ret = self.copy()
        ret.x *= k
        ret.y *= k
        return ret

    __rmul__ = __mul__

    def __floordiv__(self, k):
        ret = self.copy()
        ret.x /= k
        ret.y /= k
        return ret

    __truediv__ = __floordiv__

    def norm(self):
        return pow(pow(self.x, 2) + pow(self.y, 2), 0.5)

    def __str__(self) -> str:
        return f'({self.x},{self.y},{self.point_type},{self.limit_v})'
