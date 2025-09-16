import logging

from protocol_adapter.huawei_model.actuator_info import ActuatorInfo
from protocol_adapter.huawei_model.const import get_int_dat

_logger = logging.getLogger(__name__)


class ArmInfo(ActuatorInfo):
    def __init__(self):
        super().__init__()
        self.action_id = 250
        self.action_param0 = 0
        self.action_param1 = 0
        self.action_load_pos_type = 0
        self.action_load_row_index = 0
        self.action_load_arrange_index = 0
        self.action_unload_pos_type = 0
        self.action_unload_row_index = 0
        self.action_unload_arrange_index = 0
        self.action_exten_pos_x = 0
        self.action_exten_pos_y = 0
        self.load_shelf_id = ''
        self.unload_shelf_id = ''

    def from_dat(self, dat):
        if len(dat) < 62:
            _logger.error(f'Invalid arm data length {len(dat)}')
            return False
        self.action_load_pos_type = get_int_dat(dat, 14, 4)
        self.action_load_row_index = get_int_dat(dat, 18, 4)
        self.action_load_arrange_index = get_int_dat(dat, 22, 4)
        self.action_unload_pos_type = get_int_dat(dat, 42, 4)
        self.action_unload_row_index = get_int_dat(dat, 46, 4)
        self.action_unload_arrange_index = get_int_dat(dat, 50, 4)
        self.action_exten_pos_x = get_int_dat(dat, 54, 4)
        self.action_exten_pos_y = get_int_dat(dat, 58, 4)
        self.load_shelf_id = bytes.decode(dat[2:10], 'utf-8')
        self.unload_shelf_id = bytes.decode(dat[30:38], 'utf-8')
