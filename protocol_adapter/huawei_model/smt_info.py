import logging
from dataclasses import dataclass

from protocol_adapter.huawei_model.const import get_int_dat

_logger = logging.getLogger(__name__)


@dataclass
class SmtActuatorUnit:
    """表示AGV工装机构的状态数据

    # NOTE: 10.1.4.3 执行机构信息
    """

    # 单字节字段（uint8_t）
    index: int = 0  # 机构索引 (附录A.25)
    action_type: int = 0  # 动作类型 (附录A.23)
    action_direction: int = 0  # 动作方位 (附录A.24)

    # 双字节字段
    lift_height: int = 0  # 升降高度 (int16_t, 单位mm)
    lift_speed: int = 0  # 升降速度 (uint16_t, 单位mm/s)
    adjust_width: int = 0  # 目标调整宽度 (uint16_t, 单位mm)
    adjust_width_speed: int = 0  # 调宽速度 (uint16_t, 单位mm/s)
    cargo_type: int = 0  # 货物类型同时对应宽度类型 (uint8_t)

    # 字节数组字段
    # reserved: bytes  # 预留字节 (18字节)


@dataclass
class SmtStateUnit(SmtActuatorUnit):
    docking_state: int = 0  # 对接状态
    cargo_state: int = 0  # 物料状态


class SmtInfo:
    def __init__(self):
        self.unit_ct = 4
        self.units = tuple(SmtActuatorUnit(index=i) for i in range(self.unit_ct))

    def from_dat(self, dat):
        # 执行机构类型(uint16_t)，用于标识联合体中具体的类型
        self._actuator_type = get_int_dat(dat, 0, 2, signed=False)
        dat = dat[8:]

        for i in range(self.unit_ct):
            ref = i * 24

            index = get_int_dat(dat, ref, 1, signed=False)
            if index >= self.unit_ct:
                _logger.error(f'smt info unit index out of range: {index}')
                continue

            unit = self.units[index]

            unit.index = index
            unit.action_type = get_int_dat(dat, ref + 1, 1, signed=False)
            unit.action_direction = get_int_dat(dat, ref + 2, 1, signed=False)
            unit.lift_height = get_int_dat(dat, ref + 4, 2, signed=True)
            unit.lift_speed = get_int_dat(dat, ref + 6, 2, signed=False)
            unit.adjust_width = get_int_dat(dat, ref + 8, 2, signed=False)
            unit.adjust_width_speed = get_int_dat(dat, ref + 10, 2, signed=False)
            unit.cargo_type = get_int_dat(dat, ref + 12, 1, signed=False)

    @property
    def actuator_type(self):
        return self._actuator_type

    @actuator_type.setter
    def actuator_type(self, value):
        self._actuator_type = value

    def __str__(self):
        return f'{self.units}'


class SmtState:
    def __init__(self):
        self.unit_ct = 4
        self.units = tuple(SmtStateUnit(index=i) for i in range(self.unit_ct))

    def is_load_free(self):
        return all(unit.cargo_state == 0 for unit in self.units)

    def __str__(self):
        return f'{self.units}'
