import yaml
import csv
import pathlib
import logging

from protocol_adapter.const import ActuatorType, DeviceType, DeviceSubType, ConfigKey
from protocol_adapter.utils import GeometryUtils
from protocol_adapter.lem_report.models import ReportServiceConfig


_logger = logging.getLogger(__name__)

CONFIG_PATH = [
    'config/main.yaml',
    '/etc/sros/main.yaml',
    '/sros/protocol_adapter/config/main.yaml',
]
CONFIG_FALLBACK = {
    ConfigKey.SERVER_IP: '127.0.0.1',
    ConfigKey.SERVER_PORT: 8988,
    ConfigKey.NICKNAME: '1234',
    ConfigKey.AGV_MODEL: 'Oasis-300E',
    ConfigKey.ACTUATOR_TYPE: ActuatorType.Lift_Rotate,
    ConfigKey.RACK_WIDTH: 780,
    ConfigKey.RACK_LENGTH: 1320,
    ConfigKey.STOP_DISTANCE: 1.5,
    ConfigKey.STOP_DISTANCE_BACKWARD: 1.5,
    ConfigKey.STOP_WIDTH_OFFSET: 0.03,
    ConfigKey.SLOW_DISTANCE: 2.0,
    ConfigKey.SLOW_WIDTH_OFFSET: 0.12,
    # extra
    'network.local_port': 10001,
    'path.error_code': ['config/error_code.csv'],
}

TEST_DATA_MAP = [
    {
        'dm_code': 'AB',
        'name': 'HONOR_B5_2F',
        'switch_points': [
            {'x': 57489, 'y': 24833, 'angle': 270},
            {'x': 56489, 'y': 24833, 'angle': 270},
            {'x': 57489, 'y': 26333, 'angle': 270},
            {'x': 56489, 'y': 26333, 'angle': 270},
        ],
    },
    {
        'dm_code': 'AC',
        'name': 'HONOR_B5_3F',
        'switch_points': [
            {'x': 57348, 'y': 24213, 'angle': 270},
            {'x': 56358, 'y': 24213, 'angle': 270},
            {'x': 57348, 'y': 25713, 'angle': 270},
            {'x': 56358, 'y': 25713, 'angle': 270},
        ],
    },
    {
        'dm_code': 'TK',
        'name': 'TK',
        'switch_points': [{'x': 5220, 'y': 19746, 'angle': 180}],
    },
    {
        'dm_code': 'TL',
        'name': 'TL',
        'switch_points': [{'x': 8130, 'y': 32635, 'angle': 180}],
    },
    {
        'dm_code': 'TM',
        'name': 'TM',
        'switch_points': [
            {'x': 13075, 'y': 43024, 'angle': 180},
            {'x': 167968, 'y': 255148, 'angle': 180},
        ],
    },
    {
        'dm_code': 'TD',
        'name': 'TD',
        'switch_points': [{'x': 110780, 'y': 149800, 'angle': 0}],
    },
]

TEST_DATA_ENTRY_POINTS = {
    'TK': [{'x': 5220, 'y': 18455}],
    'TM': [{'x': 167898, 'y': 253879}],
    'TD': [{'x': 110799, 'y': 148500}],
}


class Config:
    def __init__(self, path=''):
        self._path = path

        self._robot_id = 10000
        self._car_type = ActuatorType.Unknown
        self._agv_model = ''
        self._device_type = DeviceType.NONE

        self._msg_resend_internal = 0.2  # 消息重发时间间隔，单位s
        self._msg_live_time = 60  # 消息存活时间, 单位s
        self._upload_status_interval = 1  # 状态上传时间间隔1s
        self._upload_battery_status_interval = 0  # 上报电池状态时间间隔，0表示不上传

        self._is_upload_dmcode = False  # 是否上报地码

        self._allow_dispatch_task_ahead = False  # 支持提前下发任务

        # 锁格空间
        self._is_need_lock_space = True  # 是否允许旋转时不申请锁定空间
        self._lock_space_width = 0
        self._lock_space_length = 0

        self._global_precision = None  # 全局精度配置

        # 记录小车数据库中停止避障参数，分别是前、后、左、右
        self._oba_stop_params = (0, 0, 0, 0)
        # 记录小车数据库中的减速避障参数，分别是前、后、左、右
        self._oba_slow_params = (0, 0, 0, 0)

        self._error_codes = None  # 错误码

        self._maps = TEST_DATA_MAP
        self._entry_points = TEST_DATA_ENTRY_POINTS

        self.hw_state = {}
        self.mock_positions = {}
        self.report_settings = ReportServiceConfig()

        self.local_port = 0
        self.server_port = 0
        self.server_ip = 0

    def load_and_sync_config(self, name='main'):
        config = self.get_custom_config(name)
        self.sync_from_config_data(config)

    def get_custom_config(self, name='main') -> dict:
        config = {}

        for path in [self._path] + CONFIG_PATH:
            if not path:
                continue

            conf_path = pathlib.Path(path)
            if conf_path.is_file():
                _logger.info(f'load config: {conf_path} {name}')
                try:
                    with conf_path.open() as f:
                        config = yaml.safe_load(f)
                except Exception as e:
                    _logger.error(f'解析配置失败: {e}')
                break

        config_apply = config.get(name, {}).copy()
        ref_list = []
        while True:
            if 'base' in config_apply:
                ref_name = config_apply.pop('base')
                if ref_name in ref_list:
                    _logger.error(f'find recursive case ref, end at `{ref_name}`')
                    return {}

                ref_list.append(ref_name)
                ref_config = config.get(ref_name, {}).copy()
                ref_config.update(config_apply)
                config_apply = ref_config
            else:
                break

        data = CONFIG_FALLBACK.copy()
        data.update(config_apply)
        return data

    def sync_from_config_data(self, data: dict):
        self._sync_config_basic(data)
        self._sync_config_oba(data)
        self._sync_config_mock(data)
        self._sync_config_report_service(data)

    def _sync_config_basic(self, data: dict):
        self._device_type = DeviceType(data.get('device_type', 0))
        self._device_sub_type = DeviceType(data.get('device_sub_type', 0))
        dev_actuator_type = self.get_device_actuator_type(self._device_type)
        if dev_actuator_type != ActuatorType.Unknown:
            self._car_type = dev_actuator_type
            _logger.info(f'set car_type from device_type: {self._car_type:#x}')
            if self._car_type == ActuatorType.Smt and self._device_sub_type == DeviceSubType.Aging:
                self._car_type = ActuatorType.Aging

        if self._car_type == ActuatorType.Unknown:
            if ConfigKey.ACTUATOR_TYPE in data:
                self._car_type = ActuatorType(int(data[ConfigKey.ACTUATOR_TYPE]))
                _logger.info(f'set car_type: {self._car_type:#x}')

        if ConfigKey.AGV_MODEL in data:
            self._agv_model = data[ConfigKey.AGV_MODEL]
            _logger.info(f'set agv_model: {self._agv_model}')

        nickname = data.get(ConfigKey.NICKNAME)
        if isinstance(nickname, str) and nickname.isdigit():
            self._robot_id = int(nickname)
            _logger.info(f'set robot id: {self._robot_id}')

        server_ip = data.get(ConfigKey.SERVER_IP)
        if server_ip is not None:
            self.server_ip = server_ip

        server_port = data.get(ConfigKey.SERVER_PORT)
        if server_port is not None:
            self.server_port = int(server_port)

        local_port = data.get('network.local_port')
        if local_port is not None:
            self.local_port = int(local_port)
            _logger.info(f'set local port: {self.local_port}')

        if 'path.error_code' in data:
            path_list = data.get('path.error_code')
            if isinstance(path_list, str):
                path_list = [path_list]
            if isinstance(path_list, list):
                for path in path_list:
                    if self.init_error_codes(path):
                        break
                else:
                    _logger.warning('find no error_code.csv')

    def _sync_config_oba(self, data: dict):
        if ConfigKey.RACK_WIDTH in data:
            self._lock_space_width = int(data[ConfigKey.RACK_WIDTH])
            _logger.info(f'set lock area width: {self._lock_space_width}')
        if ConfigKey.RACK_LENGTH in data:
            self._lock_space_length = int(data[ConfigKey.RACK_LENGTH])
            _logger.info(f'set lock area length: {self._lock_space_length}')

        stop_params = (
            data.get(ConfigKey.STOP_DISTANCE),
            data.get(ConfigKey.STOP_DISTANCE_BACKWARD),
            data.get(ConfigKey.STOP_WIDTH_OFFSET),
            data.get(ConfigKey.STOP_WIDTH_OFFSET),
        )
        if None not in stop_params:
            self._oba_stop_params = tuple(int(float(x) * 1000) for x in stop_params)  # type: ignore
            _logger.info(f'set oba stop params: {self._oba_stop_params}')

        slow_params = (
            data.get(ConfigKey.SLOW_DISTANCE),
            0,
            data.get(ConfigKey.SLOW_WIDTH_OFFSET),
            data.get(ConfigKey.SLOW_WIDTH_OFFSET),
        )
        if None not in slow_params:
            self._oba_slow_params = tuple(int(float(x) * 1000) for x in slow_params)  # type: ignore
            _logger.info(f'set oba slow params: {self._oba_slow_params}')

    def _sync_config_report_service(self, data: dict):
        if 'report' in data:
            self.report_settings = ReportServiceConfig.model_validate(
                data['report'], from_attributes=True
            )

    def _sync_config_mock(self, data: dict):
        if 'mock_positions' in data:
            self.mock_positions = data['mock_positions']

        if 'hw_state' in data:
            self.hw_state = data['hw_state']

    def set_robot_id(self, robot_id: int):
        self._robot_id = robot_id

    def get_map(self, point):
        for map_item in self._maps:
            for p in map_item['switch_points']:
                if GeometryUtils.is_same_pose(point, p, ignore_angle=True):
                    return map_item
        return None

    def get_map_by_dm_code(self, dm_code):
        for map_item in self._maps:
            if map_item['dm_code'] in dm_code:
                return map_item['name']
        return ''

    def is_entry_lift_point(self, targetx, targety, map_name):
        if map_name in self._entry_points:
            for points in self._entry_points[map_name]:
                if points['x'] == targetx and points['y'] == targety:
                    return True
        return False

    def get_dm_code_by_map(self, map_name):
        for map_item in self._maps:
            if map_item['name'] == map_name:
                return map_item['dm_code']
        return map_name

    def get_robot_id(self) -> int:
        return self._robot_id

    def is_device_riser(self):
        return self._car_type == ActuatorType.Lift and not self.is_agv_model_gulf()

    def is_device_riser_rotate(self):
        return self._car_type == ActuatorType.Lift_Rotate and not self.is_agv_model_gulf()

    def is_device_single_roller(self):
        return self._car_type == ActuatorType.Roller

    def is_device_dlayer_roller(self):
        return self._car_type == ActuatorType.Double_Layer_Roller

    def is_device_drow_layer(self):
        return self._car_type == ActuatorType.Double_Row_Roller

    def is_device_smt(self):
        return self._car_type == ActuatorType.Smt

    def is_device_aging(self):
        return self._car_type == ActuatorType.Aging

    def is_device_roller(self):
        return (
            self.is_device_single_roller()
            or self.is_device_dlayer_roller()
            or self.is_device_drow_layer()
        ) and not self.is_agv_model_gulf()

    def is_device_all_direction(self):
        return self._car_type == ActuatorType.Smt or (
            self._car_type == ActuatorType.All_Direction and not self.is_agv_model_gulf()
        )

    def get_device_actuator_type(self, device_type: DeviceType) -> ActuatorType:
        """获取执行结构类型，当设备类型有定义时，由设备类型导出"""

        device_type_map = {
            DeviceType.RISER: ActuatorType.Lift_Rotate,
            DeviceType.ROLLER: ActuatorType.Roller,
            DeviceType.SMT: ActuatorType.Smt,
            DeviceType.AGING: ActuatorType.Aging,
        }
        return device_type_map.get(device_type, ActuatorType.Unknown)

    def get_device_type(self):
        """获取设备类型，当设备类型未直接定义时，从执行机构类型推导"""
        if self._device_type != DeviceType.NONE:
            return self._device_type

        if self.is_device_roller():
            return DeviceType.ROLLER
        elif self.is_device_smt():
            return DeviceType.SMT
        elif self.is_device_aging():
            return DeviceType.AGING
        elif (
            self.is_device_riser()
            or self.is_device_riser_rotate()
            or self.is_device_all_direction()
        ):
            return DeviceType.RISER
        elif self.is_agv_model_gulf():
            return DeviceType.GULF

        return DeviceType.NONE

    def init_error_codes(self, file_path: str) -> bool:
        path = pathlib.Path(file_path)
        if not file_path or not path.exists():
            return False

        _logger.info(f'load error_code from: {file_path}')
        try:
            with path.open() as f:
                reader = csv.DictReader(f, fieldnames=['id', 'name', 'desc', 'method', 'valid'])
                items = []
                for row in reader:
                    if row['id'].isdigit():
                        row['id'] = int(row['id'])
                        items.append(row)

            self._error_codes = items
            return True
        except Exception as e:
            _logger.error(f'failed to load error_code: {e}')
            return False

    def set_lock_space_area(self, width, length):
        self._lock_space_width = width
        self._lock_space_length = length

    def get_lock_space_area(self):
        return self._lock_space_width, self._lock_space_length

    def set_car_type(self, car_type: ActuatorType):
        self._car_type = car_type

    def get_car_type(self) -> ActuatorType:
        return self._car_type

    def set_msg_resend_interval(self, interval):
        self._msg_resend_internal = interval

    def get_msg_resend_interval(self):
        return self._msg_resend_internal

    def set_msg_live_time(self, live_time):
        self._msg_live_time = live_time

    def get_msg_live_time(self):
        return self._msg_live_time

    def set_upload_status_interval(self, second):
        if second <= 0:
            return
        self._upload_status_interval = second

    def get_upload_status_interval(self):
        return self._upload_status_interval

    def set_upload_battery_status_interval(self, second):
        if second < 0:
            return
        self._upload_battery_status_interval = second

    def get_upload_battery_status_interval(self):
        return self._upload_battery_status_interval

    def set_global_precision(self, cfg):
        self._global_precision = cfg

    def get_global_precision(self):
        return self._global_precision

    def get_resend_times(self):
        return int(self._msg_live_time / self._msg_resend_internal)

    def set_upload_dmcode_status(self, enable):
        self._is_upload_dmcode = enable

    def is_upload_dmcode(self):
        return self._is_upload_dmcode

    def get_is_need_lock_space(self):
        return self._is_need_lock_space

    def set_is_need_lock_space(self, is_lock):
        self._is_need_lock_space = is_lock

    def get_allow_dispatch_task_ahead(self):
        return self._allow_dispatch_task_ahead

    def set_allow_dispatch_task_ahead(self, allowed):
        self._allow_dispatch_task_ahead = allowed

    def set_oba_stop_params(self, val):
        _logger.info(f'set oba stop params: {val}')
        self._oba_stop_params = val

    def get_oba_stop_params(self):
        return self._oba_stop_params

    def set_oba_slow_params(self, val):
        _logger.info(f'set oba slow params: {val}')
        self._oba_slow_params = val

    def get_oba_slow_params(self):
        return self._oba_slow_params

    def set_agv_model(self, val):
        self._agv_model = val

    def is_agv_model_gulf(self):
        return self._agv_model.find('ulf') >= 0
