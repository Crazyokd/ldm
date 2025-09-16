from protocol_adapter.huawei_model.actuator_info import ActuatorInfo
from protocol_adapter.huawei_model.const import (
    get_int_dat,
    ROLLER_ACTION_NONE,
    ROLLER_DIR_LEFT_OR_FORWARD,
)


class RollerInfo(ActuatorInfo):
    def __init__(
        self, action_type=ROLLER_ACTION_NONE, direction=ROLLER_DIR_LEFT_OR_FORWARD, cargo_count=0
    ):
        self.action_type = action_type
        self.direction = direction
        self.cargo_count = cargo_count

    def from_dat(self, dat):
        if len(dat) < 4:
            return
        self.action_type = get_int_dat(dat, 0, 1)
        self.direction = get_int_dat(dat, 1, 1)
        self.cargo_count = get_int_dat(dat, 2, 1)

    def is_valid(self):
        return self.cargo_count != 0
