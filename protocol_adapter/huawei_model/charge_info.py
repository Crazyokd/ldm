import socket

from protocol_adapter.huawei_model.base import Base
from protocol_adapter.huawei_model.const import get_int_dat, ChargeFlag


class ChargeInfo(Base):
    def __init__(self):
        self.charge_flag = ChargeFlag.Start_Charge
        self.charge_time = 20  # 单位分钟
        self.charge_id = 0  # 充电桩id
        self.charge_ip = ''  # 充电桩IP

    def from_dat(self, dat):
        if len(dat) < 12:
            return

        self.charge_flag = get_int_dat(dat, 0, 2)
        self.charge_time = get_int_dat(dat, 2, 2)
        self.charge_id = get_int_dat(dat, 4, 2)
        self.charge_ip = socket.inet_ntop(socket.AF_INET, dat[8:12])

    def get_charge_time_in_second(self):
        return self.charge_time * 60

    def get_charge_ip(self):
        return self.charge_ip

    def is_start_charge(self):
        return self.charge_flag == ChargeFlag.Start_Charge

    def is_stop_charge(self):
        return self.charge_flag == ChargeFlag.Stop_Charge
