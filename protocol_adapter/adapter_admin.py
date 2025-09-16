import logging
import argparse
import threading
import time

from abc import ABC
from typing import Optional

from protocol_adapter.version import version_details
from protocol_adapter.utils import SrosLog, ThreadTask
from protocol_adapter.config import Config
from protocol_adapter.const import ActuatorType, DeviceType
from protocol_adapter.protobuf_wrapper.base import Pose
from protocol_adapter.adapter_huawei_protocol import HuaweiProtocolAdapter
from protocol_adapter.srp_wrapper import SrpWrapper

_logger = logging.getLogger(__name__)

CONNECT_RETRY_INTERVAL = 5


class AdapterCore(ABC):
    _args: argparse.Namespace
    _config: Config

    _srp_wrapper: SrpWrapper
    _adapter_huawei_protocol: HuaweiProtocolAdapter

    def start(self):
        self._srp_wrapper = SrpWrapper(
            mock=self._args.mock, mock_actuator=self._config.get_car_type()
        )
        self._srp_wrapper.add_callbacks_connect_state(self.on_sros_connected_changed)
        self._srp_wrapper.add_system_state_callback(self.on_sys_state)

        self._adapter_huawei_protocol = HuaweiProtocolAdapter(self._srp_wrapper, self._config)

        self._sros_connector = ThreadTask(
            on_retry=self.try_sros_login,
            on_success=self.on_sros_login_success,
            retry_interval=CONNECT_RETRY_INTERVAL,
            name='sros_connector',
        )
        self._sros_connector.start(delay=0 if self._args.mock else CONNECT_RETRY_INTERVAL)

    def try_sros_login(self):
        _logger.info('connect to sros ..')
        return self._srp_wrapper.login(self._args.sros_ip, 'admin', 'admin')

    def on_sros_login_success(self):
        _logger.info('login sros success')
        if not self._args.mock:
            time.sleep(1)
        if not self._adapter_huawei_protocol:
            self._adapter_huawei_protocol = HuaweiProtocolAdapter(self._srp_wrapper, self._config)
        if not self._args.mock:
            time.sleep(10)
        self._adapter_huawei_protocol.start()

    def on_sros_connected_changed(self, is_connected):
        _logger.info('Connect state changed: ' + str(is_connected))
        if self._adapter_huawei_protocol._task_thread.is_cur_task_running():
            _logger.info('clear task thread')
            self._adapter_huawei_protocol.reset_task_state()
        if not is_connected:
            self._sros_connector.start(delay=0.5)

    def on_sys_state(self, state):
        self._sros_connector.stop()

    def stop(self):
        if self._adapter_huawei_protocol:
            self._adapter_huawei_protocol.stop()
        self._srp_wrapper.stop()
        self._sros_connector.stop()


class AdapterTestInterface(ABC):
    _args: argparse.Namespace
    _srp_wrapper: SrpWrapper

    def set_sros_pose(self, pose, **kwargs):
        """测试专用，设置车辆的初始位置"""
        assert self._args.mock
        self._srp_wrapper.set_sros_pose(pose, **kwargs)

    def set_hw_state(self, **kwargs):
        """测试接口，设置硬件状态"""
        assert self._args.mock
        self._srp_wrapper.set_hw_state(**kwargs)

    def get_sros_plate_angle(self):
        """获取顶板角度(相对小车的角度)"""
        return self._srp_wrapper.get_shelf_angle_to_robot()

    def get_sros_cur_v(self):
        """获取小车当前速度 mm/s"""
        return self._srp_wrapper.get_linear_velocity()


class AdapterAdmin(AdapterCore, AdapterTestInterface):
    def __init__(self, *, mock=False, device_type=DeviceType.NONE):
        # 以命令行默认参数初始化，再使用类初始化参数覆盖
        self._args = self.parse_args([])
        self._args.mock = mock
        self._args.device_type = device_type

    def run(self, argv: Optional[list] = None, *, wait=False):
        # 如果有指定运行参数，以运行参数为准
        if argv:
            self._args = self.parse_args(argv)

        if self._args.version:
            print(f'version: {version_details}')
            return

        self.setup_log()
        self.setup_uvloop()
        self.handle_signals()

        _logger.info(f'>> protocol_adapter ver: {version_details}')

        self.load_config_and_setup_if_mock()
        self.start()
        self.load_init_state_from_world_if_mock()

        if wait:
            # 等待其它线程结束: 主线程结束后，向线程池提交新任务会出错
            while threading.active_count() > 1:
                time.sleep(1)

    def load_config_and_setup_if_mock(self):
        self._config = Config(path=self._args.config)
        self._config.load_and_sync_config('mock' if self._args.mock else 'main')

        if self._args.mock:
            dev_actuator_type = self._config.get_device_actuator_type(self._args.device_type)
            if dev_actuator_type != ActuatorType.Unknown:
                _logger.warning(f'mock with device_type: {self._args.device_type:#x}')
                self._config._device_type = self._args.device_type
                self._config.set_car_type(dev_actuator_type)

            if self._config.mock_positions:
                from protocol_adapter.mock.world_mock import WorldMock

                world = WorldMock()
                world.load_mock_positions(self._config.mock_positions)

    def load_init_state_from_world_if_mock(self):
        """从世界加载初始位姿信息"""
        if not self._args.mock:
            return

        from protocol_adapter.mock.world_mock import WorldMock

        world = WorldMock()
        init_pose = world.init_pose

        pose = init_pose.get('pose')
        map_name = init_pose.get('map')
        shelf_info = init_pose.get('shelf')

        if pose:
            pose = Pose(*pose)

        shelf_pose = None
        shelf_id = ''

        if shelf_info and pose:
            shelf_id, shelf_angle = shelf_info
            shelf_pose = Pose(x=pose.x, y=pose.y, yaw=shelf_angle)

        if pose:
            self.set_sros_pose(pose, shelf_pose=shelf_pose, shelf_id=shelf_id, map_name=map_name)

        if self._config.hw_state:
            self.set_hw_state(**self._config.hw_state)

    def parse_args(self, argv: list) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            prog='protocol_adapter', description='protocol adapter for RCS'
        )

        parser.add_argument('--config', default='config/main.yaml', help='config file')
        parser.add_argument('--sros-ip', default='127.0.0.1', help='sros ip', metavar='IP')
        parser.add_argument('--mock', help='run simulation with mock', action='store_true')
        parser.add_argument(
            '--device-type',
            default=DeviceType.NONE,
            type=lambda x: int(x, 0),
            help='the device type to select: {1, 2, 8}',
            metavar='TYPE',
        )
        parser.add_argument(
            '--log-level', default='info', help='log level, default: INFO', metavar='LEVEL'
        )
        parser.add_argument(
            '--log-dir', default='', help='log directory, default no file log', metavar='DIR'
        )
        parser.add_argument('-v', '--verbose', help='enable log in console', action='store_true')
        parser.add_argument('-V', '--version', help='print version and exit', action='store_true')

        return parser.parse_args(argv)

    def setup_log(self):
        sros_log = SrosLog('protocol_adapter')

        # 转换日志等级
        if self._args.log_level.isdigit():
            log_level = int(self._args.log_level)
        else:
            log_level = getattr(logging, self._args.log_level.upper())

        if self._args.verbose:
            sros_log.sendLogToConsole(level=log_level)

        if self._args.log_dir:
            sros_log.sendLogToFile(level=log_level, directory=self._args.log_dir)
        else:
            _logger.debug('no logging to file')

        # let other loggers quiet
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)

    def setup_uvloop(self):
        try:
            import uvloop
        except ImportError:
            _logger.warning('failed to import uvloop, fallback to asyncio')
            return
        else:
            import asyncio

            _logger.debug('asyncio set to uvloop')
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    def handle_signals(self):
        def handler_on_exit(signum, frame):
            _logger.info(f'get signal: {signum} on {frame}')
            self.stop()

        # import signal
        # TODO: zz 捕获 SIGTERM 导致 sros 服务重启时，适配器进程不能正常退出(待排查)
        # signal.signal(signal.SIGTERM, handler_on_exit)
        # signal.signal(signal.SIGINT, handler_on_exit)
