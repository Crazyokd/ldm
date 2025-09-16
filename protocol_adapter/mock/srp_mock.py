#!/usr/bin/python3
# Copyright 2024 Standard Robots Co. All rights reserved.
import logging
import sys

from protocol_adapter.version import version_package
from protocol_adapter.config import Config
from protocol_adapter.huawei_model.smt_info import SmtState
from protocol_adapter.mock.smt_actuator_mock import SmtActuatorMock
from protocol_adapter.protobuf_wrapper import main_pb2
from protocol_adapter.mock.sros_mock import SrosMock
from protocol_adapter.const import ActuatorType, ConfigKey

_logger = logging.getLogger(__name__)


class SrpMock:
    def __init__(self, actuator_type=ActuatorType.Lift_Rotate):
        self._sros = SrosMock(actuator_type=actuator_type)
        self._sros.run()

        # load config for mock
        self._mock_config = Config().get_custom_config('mock')
        self._mock_config[ConfigKey.ACTUATOR_TYPE] = actuator_type

    def stop(self):
        self._sros.stop()

    def set_callback_connect(self, fun):
        self._sros.set_callback_connect(fun)

    def set_system_state_callback(self, fun):
        self._sros.set_system_state_callback(fun)

    def set_hardware_state_callback(self, fun):
        self._sros.set_hardware_state_callback(fun)

    def set_sensor_samples_callback(self, fun):
        self._sros.set_sensor_samples_callback(fun)

    def set_laser_point_callback(self, fun):
        self._sros.set_laser_point_callback(fun)

    def set_notify_move_task_finished_callback(self, fun):
        self._sros.set_notify_move_task_finished_callback(fun)

    def set_notify_action_task_finished_callback(self, fun):
        self._sros.set_notify_action_task_finished_callback(fun)

    def set_notify_mission_list_change_callback(self, fun):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def on_system_state(self, sys_state):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def on_move_task_finish(self, notification):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def on_action_task_finish(self, notification):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def set_location_result(self, result):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def login(self, ip_addr, user_name, passwd) -> bool:
        _logger.info(f'login {ip_addr} ** ******')
        return True

    def logout(self):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def fetch_system_state(self):
        self._sros._update_system_state()

    def fetch_hardware_state(self):
        self._sros._update_hardware_state()

    def fetch_sensor_samples(self):
        self._sros._update_sensor_samples()

    def get_smt_state(self) -> SmtState:
        if isinstance(self._sros._actuator, SmtActuatorMock):
            return self._sros._actuator.state
        else:
            raise AssertionError('not smt actuator')

    def get_sros_config(self, key):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def get_sros_configs(self, keys: list) -> dict:
        return {key: self._mock_config.get(key) for key in keys}

    def set_sros_cache_configs(self, configs):
        self._sros.set_sros_cache_configs(configs)

    def get_info(self):
        return main_pb2.Info(
            serial_no='R2D2',
            nickname=self._mock_config[ConfigKey.NICKNAME],
            hardware_version='0.0.2',
            sros_version_str=version_package,
            src_version_str='0.2.1',
            vehicle_serial_no='0.0.0.0.0.0',
        )

    def set_manual_control(self, is_manual: bool):
        if is_manual:
            self._sros.enable_manual_control()
        else:
            self._sros.disable_manual_control()

    def set_traffic_control(self, enable: bool):
        if enable:
            self._sros.enable_traffic_control()
        else:
            self._sros.disable_traffic_control()

    def triger_emergency(self):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def cancel_emergency(self):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def move_to_station(
        self, no, station_id, avoid_policy=main_pb2.MovementTask.OBSTACLE_AVOID_WAIT
    ):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def move_follow_path(
        self,
        no,
        paths,
        cancel_task_decetect_dmcode,
        avoid_policy=main_pb2.MovementTask.OBSTACLE_AVOID_WAIT,
    ):
        self._sros.move_follow_path(no, paths, cancel_task_decetect_dmcode)

    # 追加路径
    def replace_move_path(self, no, paths, cancel_task_decetect_dmcode):
        self._sros.replace_move_path(paths)

    def pause_task(self):
        self._sros.pause_task()

    def continue_task(self):
        self._sros.continue_task()

    def cancel_task(self):
        self._sros.cancel_task()

    def cancel_movement_task(self, soft_cancel):
        self._sros.cancel_movement_task(soft_cancel)

    def stop_location(self):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def set_current_map(self, map_name):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def start_location(
        self, map_name: str, x, y, angle, x_factor, y_factor, absolute_location=False, timeout=60
    ) -> bool:
        return self._sros.map_switching(map_name, x / 1000, y / 1000, angle, absolute_location)

    def start_charge(self, seq):
        self._sros.start_charge()

    def stop_charge(self, seq):
        self._sros.stop_charge()

    # 同步执行，直到动作结果返回或超时
    def execute_action_task(self, no, action_id, param0, param1, paramStr=''):
        return self._sros.sync_execute_action_task(no, action_id, param0, param1, paramStr)

    def cancel_action_task(self):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def read_input_registers(self, start_addr, count):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    # 以下为异步步指令
    def async_move_to_station(
        self, no, station_id, avoid_policy=main_pb2.MovementTask.OBSTACLE_AVOID_WAIT
    ):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def async_execute_action_task(self, no, action_id, param0, param1):
        raise NotImplementedError(
            f'未实现：{sys._getframe().f_code.co_filename}:{sys._getframe().f_lineno}'
        )

    def set_sros_pose(self, pose, **kwargs):
        self._sros.set_pose(pose, **kwargs)

    def set_hw_state(self, **kwargs):
        self._sros.set_hw_state(**kwargs)


if __name__ == '__main__':
    srp = SrpMock()
    srp.on_move_task_finish(1)
