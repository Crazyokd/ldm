import re
import time
import math
import logging

from protocol_adapter.utils import AngleUtils
from protocol_adapter.const import ActionID, ActuatorType, DeviceID, ConfigKey
from protocol_adapter.protobuf_wrapper import main_pb2, monitor_pb2

_logger = logging.getLogger(__name__)


class SrpWrapper:
    def __init__(self, *, mock=False, mock_actuator=ActuatorType.Lift_Rotate):
        self._system_state_cnt = 0
        self._path_task_no = 0

        if mock:
            from protocol_adapter.mock.srp_mock import SrpMock

            self._srp = SrpMock(actuator_type=mock_actuator)
        else:
            from protocol_adapter.protobuf_wrapper.srp import SRP

            self._srp = SRP()

        self._system_state = None
        self._hardware_state = None
        self._sensor_samples = None

        self._callbacks_system_state = []
        self._callbacks_hardware_state = []
        self._callbacks_move_task_finish = []
        self._callbacks_action_task_finish = []
        self._callbacks_low_battery = []
        self._callbacks_brake_switch_changed = []
        self._callbacks_emergency_state_changed = []
        self._callbacks_charge_finish = []
        self._callbacks_connect_state = []
        self._callbacks_dmcode_changed = []
        self._callback_map_changed = []
        self._callbacks_on_sensor_samples = []

        self._srp.set_system_state_callback(self.on_system_state)
        self._srp.set_hardware_state_callback(self.on_hardware_state)
        self._srp.set_sensor_samples_callback(self.on_sensor_samples)
        self._srp.set_notify_move_task_finished_callback(self.on_move_task_finish)
        self._srp.set_notify_action_task_finished_callback(self.on_action_task_finish)
        self._srp.set_callback_connect(self.on_connect_state_changed)

        self._is_move_at_arc = False  # 当前车辆是否运行在曲线上

    def stop(self):
        self._srp.stop()

    def login(self, ip_addr, user_name, passwd) -> bool:
        return self._srp.login(ip_addr, user_name, passwd)

    # 主动请求状态，避免由于状态上报延时导致判断错误
    def sync_robot_state(self):
        self.fetch_system_state()
        self.fetch_hardware_state()

    # 主动获取系统状态
    def fetch_system_state(self):
        try:
            return self._srp.fetch_system_state()
        except BaseException as e:
            _logger.error(e)

    # 主动请求传感器采样数据
    def fetch_sensor_samples(self):
        try:
            return self._srp.fetch_sensor_samples()
        except BaseException as e:
            _logger.error(e)

    # 主动获取硬件状态
    def fetch_hardware_state(self):
        try:
            return self._srp.fetch_hardware_state()
        except BaseException as e:
            _logger.error(e)

    def is_move_at_arc(self):
        return self._is_move_at_arc

    def move_follow_path(self, no, path, cancel_task_decetect_dmcode=False):
        _logger.info(f'[[[[[ move task {no} start:')
        try:
            self._srp.move_follow_path(no, path, cancel_task_decetect_dmcode)
            self._path_task_no = no
        except BaseException as e:
            raise e

    def replace_move_path(self, paths, cancel_task_decetect_dmcode=False):
        _logger.info(f'Replace movement paths, no={self._path_task_no}')
        self._srp.replace_move_path(self._path_task_no, paths, cancel_task_decetect_dmcode)

    def move_to_station(self, no, station_id):
        self._srp.move_to_station(no, station_id)

    def execute_action_task(self, no, action_id, param0, param1, paramStr=''):
        return self._srp.execute_action_task(no, action_id, param0, param1, paramStr)

    def start_charge(self, no):
        self._srp.start_charge(no)

    def stop_charge(self, no):
        self._srp.stop_charge(no)

    def cancel_task(self):
        self._srp.cancel_task()

    def pause_task(self):
        self._srp.pause_task()

    def continue_task(self):
        self._srp.continue_task()

    def set_manual_control(self, is_manual=True):
        self._srp.set_manual_control(is_manual)

    def set_traffic_control(self, enable: bool):
        self._srp.set_traffic_control(enable)

    def is_location_democode(self):
        return self.is_location_okay() and int(self._system_state.location_pose.confidence) == 0

    def cancel_movement_task(self, soft_cancel=False):
        self._srp.cancel_movement_task(soft_cancel)

    def start_location(self, map_name, x, y, angle, x_f=1000, y_f=1350, absolute_location=False):
        """
        :param map_name:
        :param x:
        :param y:
        :param angle: （°）
        :param absolute_location:
        :return:
        """
        _logger.info(
            f'start location: ({x}mm, {y}mm, {angle}°) absolute_location: {absolute_location}'
        )
        try:
            return self._srp.start_location(map_name, x, y, angle, x_f, y_f, absolute_location)
        except BaseException as e:
            _logger.error(e)
        return False

    def get_location_map_name(self):
        if self._system_state is None:
            return ''
        return self._system_state.map_name

    def get_info(self):
        return self._srp.get_info()

    def get_result_code(self):
        return self._srp.get_result_code()

    def get_sros_config(self, key):
        return self._srp.get_sros_config(key)

    def get_sros_configs(self, keys) -> dict:
        return self._srp.get_sros_configs(keys)

    def set_sros_cache_configs(self, configs):
        self._srp.set_sros_cache_configs(configs)

    def add_callbacks_sensor_samples(self, callback):
        self._callbacks_on_sensor_samples.append(callback)

    def add_callbacks_connect_state(self, callback):
        self._callbacks_connect_state.append(callback)

    def add_system_state_callback(self, callback):
        self._callbacks_system_state.append(callback)

    def add_hardware_state_callback(self, callback):
        self._callbacks_hardware_state.append(callback)

    def add_move_task_finish_callback(self, callback):
        self._callbacks_move_task_finish.append(callback)

    def add_action_task_finish_callback(self, callback):
        self._callbacks_action_task_finish.append(callback)

    def add_low_battery_callback(self, callback):
        self._callbacks_low_battery.append(callback)

    def add_brake_switch_changed_callback(self, callback):
        self._callbacks_brake_switch_changed.append(callback)

    def add_emergency_state_changed_callback(self, callback):
        self._callbacks_emergency_state_changed.append(callback)

    def add_charge_finish_callback(self, callback):
        self._callbacks_charge_finish.append(callback)

    def add_dmcode_changed_callback(self, callback):
        self._callbacks_dmcode_changed.append(callback)

    def add_map_changed_callback(self, callback):
        self._callback_map_changed.append(callback)

    def on_connect_state_changed(self, is_connected):
        for callback in self._callbacks_connect_state:
            callback(is_connected)

    def on_move_task_finish(self, move_task):
        for callback in self._callbacks_move_task_finish:
            callback(move_task)

    def on_action_task_finish(self, action_task):
        for callback in self._callbacks_action_task_finish:
            callback(action_task)

    # 充电完成，电量已充满
    def on_charge_finish(self):
        for callback in self._callbacks_charge_finish:
            callback()

    def on_low_battery(self, percent):
        for callback in self._callbacks_low_battery:
            callback(percent)

    def on_dmcode_changed(self, dmcode):
        for callback in self._callbacks_dmcode_changed:
            callback(dmcode)

    def get_is_move_at_arc_state(self, system_state: main_pb2.SystemState):
        if system_state.HasField('movement_state'):
            movement_state = system_state.movement_state
            if (
                movement_state.state
                in (
                    main_pb2.MovementTask.TaskState.MT_RUNNING,
                    main_pb2.MovementTask.TaskState.MT_PAUSED,
                    main_pb2.MovementTask.TaskState.MT_WAIT_FOR_CHECKPOINT,
                    main_pb2.MovementTask.TaskState.MT_IN_CANCEL,
                )
                and movement_state.cur_path_no != 0
            ):
                path_type = movement_state.paths[movement_state.cur_path_no - 1].type
                if path_type in (main_pb2.Path.PATH_BEZIER, main_pb2.Path.PATH_CIRCLE):
                    return True
        return False

    def on_system_state(self, system_state: main_pb2.SystemState):
        # 第一时间更新系统状态，保证回调被调用时查看的状态是最新状态
        current_system_state = self._system_state
        self._system_state = system_state
        if current_system_state:
            if (
                current_system_state.location_state
                != main_pb2.SystemState.LocationState.LOCATION_STATE_RUNNING
                and system_state.location_state
                == main_pb2.SystemState.LocationState.LOCATION_STATE_RUNNING
            ):
                self._srp.set_location_result(True)

            if (
                current_system_state.location_state
                != main_pb2.SystemState.LocationState.LOCATION_STATE_NONE
                and system_state.location_state
                == main_pb2.SystemState.LocationState.LOCATION_STATE_NONE
            ):
                # self._srp.set_location_result(False)
                pass

            for callback in self._callback_map_changed:
                callback(system_state.map_name)

            if current_system_state.emergency_state != system_state.emergency_state:
                is_emergency = True
                if system_state.emergency_state in (
                    main_pb2.SystemState.EmergencyState.STATE_EMERGENCY_NONE,
                    main_pb2.SystemState.EmergencyState.STATE_EMERGENCY_NA,
                ):
                    is_emergency = False
                for callback in self._callbacks_emergency_state_changed:
                    callback(is_emergency)
            self._is_move_at_arc = self.get_is_move_at_arc_state(current_system_state)

        for callback in self._callbacks_system_state:
            callback(system_state)

    def on_hardware_state(self, hardware_state):
        # print(hardware_state)
        current_state = self._hardware_state
        self._hardware_state = hardware_state
        try:
            if current_state and hardware_state:
                if current_state.break_sw_state != hardware_state.break_sw_state:
                    self.on_brake_sw_changed(hardware_state.break_sw_state)
                if (
                    current_state.battery_percentage < 95
                    and hardware_state.battery_percentage >= 95
                ):
                    self.on_charge_finish()
                if (
                    current_state.battery_percentage >= 20
                    and hardware_state.battery_percentage < 20
                ):
                    self.on_low_battery(hardware_state.battery_percentage)
                last_dmcode, last_pose = self.get_dmcode_sn(current_state)
                current_dmcode, current_pose = self.get_dmcode_sn(hardware_state)
                # print("last: " + last_dmcode + " current: " + current_dmcode)
                if current_dmcode not in ('-', ''):
                    # 此处不代表dmcode改变,只有有值就回调，从而保证回调函数捕捉dmcode从无到有的状态，是否改变由回调函数检查，否则回调可能未注册,没有捕捉到第一dmcode值
                    self.on_dmcode_changed(current_dmcode)

            for callback in self._callbacks_hardware_state:
                callback(hardware_state)
        except BaseException as e:
            _logger.error(e, exc_info=True)

    def on_sensor_samples(self, sensor_samples: monitor_pb2.SensorDataCollection):
        self._sensor_samples = sensor_samples
        for callback in self._callbacks_on_sensor_samples:
            callback(sensor_samples)

    # 解抱闸状态变化时调用该回调, is_brake_on表示解抱闸状态（可推动）
    def on_brake_sw_changed(self, is_brake_on):
        for callback in self._callbacks_brake_switch_changed:
            callback(is_brake_on)

    # 判断是否正在执行动作任务
    def is_executing_action(self):
        action_task_state = self.get_action_task_state()
        return action_task_state not in (
            main_pb2.ActionTask.TaskState.AT_ZERO,
            main_pb2.ActionTask.TaskState.AT_FINISHED,
        )

    def is_raising_shelf(self):
        if self.is_executing_action() is False:
            return False
        action_task = self._system_state.action_state
        if action_task is None:
            return False
        return action_task.id == 4 and action_task.param0 == 1

    def is_putting_shelf(self):
        if self.is_executing_action() is False:
            return False
        action_task = self._system_state.action_state
        if action_task is None:
            return False
        return action_task.id == 4 and action_task.param0 == 2

    def is_arm_action_executing(self):
        if self.is_executing_action() is False:
            return False
        action_task = self._system_state.action_state
        if action_task is None:
            return False
        return action_task.id >= 192

    def is_rolling_action(self):
        if self.is_executing_action() is False:
            return False
        action_task = self._system_state.action_state
        if action_task is None:
            return False
        return action_task.id == 23 and action_task.param0 in (1, 2)

    def get_action_task_state(self):
        if self._system_state is None:
            return main_pb2.ActionTask.TaskState.AT_ZERO
        action_task = self._system_state.action_state
        if action_task is None:
            return main_pb2.ActionTask.TaskState.AT_ZERO
        return action_task.state

    def get_action_task_result(self):
        if self._system_state is None:
            return main_pb2.TASK_RESULT_NA, 0
        action_task = self._system_state.action_state
        if action_task is None:
            return main_pb2.TASK_RESULT_NA, 0
        return action_task.result, action_task.result_code

    def is_action_task_finished(self):
        return self.get_action_task_state() == main_pb2.ActionTask.TaskState.AT_FINISHED

    def is_action_task_failed(self):
        result, _ = self.get_action_task_result()
        return result == main_pb2.TASK_RESULT_FAILED

    # 是否是顶升动作任务
    def is_rotate_raise_shelf_action(self):
        action_task = self._system_state.action_state
        if action_task is None:
            return False
        return action_task.id == 4 and action_task.param0 == 1

    def is_rotate_put_shelf_action(self):
        action_task = self._system_state.action_state
        if action_task is None:
            return False
        return action_task.id == 4 and action_task.param0 == 2

    def is_detect_action_task_finish(self, detect_action_no):
        action_no, action_id, action_param0, action_param1 = self.get_action_task_param()
        return (
            detect_action_no == action_no
            and action_id == ActionID.DETECT_SVC
            and self.is_action_task_finished()
        )

    def is_emergency_state(self):
        return self.get_emergency_state() != main_pb2.SystemState.STATE_EMERGENCY_NONE

    # 碰撞触发急停
    def is_emergency_cause_by_hit(self):
        if self.is_emergency_state() is False:
            return False
        return 0x21 <= self._system_state.emergency_source <= 0x24

    # 解抱闸状态
    def is_brake_sw_on(self):
        if self._hardware_state is None:
            return True
        return (
            self._hardware_state.break_sw_state
            == main_pb2.HardwareState.BreakSwitchState.BREAK_SW_ON
        )

    def is_fault_error(self):
        if self._system_state is None:
            return True
        for fault in self._system_state.faults:
            if fault.response_behavior != 0:
                _logger.error(f'fault id is {fault.id}')
                return True
        return False

    # 定位失败
    def is_location_error(self):
        if self._system_state is None:
            return True
        return self._system_state.location_state in (
            main_pb2.SystemState.LocationState.LOCATION_STATE_NONE,
            main_pb2.SystemState.LocationState.LOCATION_STATE_ERROR,
        )

    def is_location_okay(self):
        if self._system_state is None:
            return False
        return (
            self._system_state.location_state
            == main_pb2.SystemState.LocationState.LOCATION_STATE_RUNNING
        )

    def is_charging(self):
        if self._hardware_state is None:
            return False
        return (
            self._hardware_state.battery_state
            == main_pb2.HardwareState.BatteryState.BATTERY_CHARGING
        )

    def is_system_idle(self):
        if self._system_state is None:
            return False
        return self._system_state.sys_state == main_pb2.SystemState.SYS_STATE_IDLE

    def is_load_full(self):
        """小车载货状态，是否满载(顶着货架)"""
        if self._system_state is None:
            return False
        return self._system_state.load_state == main_pb2.SystemState.LOAD_FULL

    # load_free 和 load_full不能互斥，sros刚起来可能处于未知状态
    def is_load_free(self):
        if self._system_state is None:
            return False
        return self._system_state.load_state == main_pb2.SystemState.LOAD_FREE

    def get_movement_task_path_length(self):
        if self._system_state is None or self._system_state.movement_state is None:
            return 0

        paths = self._system_state.movement_state.paths
        if paths is None:
            return 0
        return len(self._system_state.movement_state.paths)

    def get_action_task_param(self):
        if self._system_state is None:
            return 0, 0, 0
        action_task = self._system_state.action_state
        if action_task is None:
            return 0, 0, 0, 0
        return action_task.no, action_task.id, action_task.param0, action_task.param1

    def get_action_no(self):
        if self._system_state is None:
            return 0
        action_task = self._system_state.action_state
        if action_task is None:
            return 0
        return action_task.no

    def get_move_remain_distance(self):
        if self._system_state is None or self._system_state.movement_state is None:
            return 0
        return int(self._system_state.movement_state.remain_distance * 10)

    # 当前系统状态
    def get_sys_state(self):
        if self._system_state is None:
            _logger.warning('system state is None, maybe connect to sros failed')
            return main_pb2.SystemState.SYS_STATE_ERROR  # 错误
        return self._system_state.sys_state

    # 当前系统操作模式
    def get_operation_state(self):
        if self._system_state is None:
            _logger.warning('system state is None, maybe connect to sros failed')
            return main_pb2.SystemState.OPERATION_NONE  # 错误
        return self._system_state.operation_state

    # 获取货架当前相对于车的角度
    def get_shelf_angle_to_robot(self):
        try:
            rotate = self._system_state.rotate_value
            angle = AngleUtils.normalize_360(math.degrees(rotate / 1000))
            return angle
        except BaseException as e:
            _logger.error(e)
            return 0

    def get_fork_height(self):
        try:
            return self._system_state.forklift_state.arm_height
        except BaseException as e:
            _logger.error(e)
            return 0

    def get_smt_state(self):
        return self._srp.get_smt_state()

    # 获取货架在地图坐标系中的角度
    def get_shelf_angle_in_global(self, limit=360):
        # 华为定义的货架０度是x负方向，正常是x正方向，相差180度????
        if limit == 360:  # noqa: PLR2004
            angle_normalize = AngleUtils.normalize_360
        elif limit == 180:  # noqa: PLR2004
            angle_normalize = AngleUtils.normalize_180
        else:
            raise AssertionError(f'invalid angle limit: {limit}')

        return angle_normalize(self.get_shelf_angle_to_robot() + self.get_cur_angle())

    def get_emergency_state(self):
        return self._system_state.emergency_state

    # 获取辊筒载荷状态，bit为１表示有货
    def get_multi_load_state(self):
        if self._system_state is None:
            return 0
        return self._system_state.multi_load_state

    def get_fault_codes(self):
        if self._system_state is None:
            return []
        return list(self._system_state.fault_codes)

    # 货架id
    def get_shelf_info(self):
        for device in list(self._hardware_state.devices):
            if device.id in (DeviceID.UP_SVC, DeviceID.UP_SVC_200):
                if device.info == '':
                    continue
                sn, x, y, yaw = self.parse_dmcode_info(device.info)
                # 0.1mm
                return sn, {
                    'x': x * 10,
                    'y': y * 10,
                    'angle': AngleUtils.normalize_360(
                        self.get_cur_angle() - math.degrees(yaw / 1000)
                    ),
                }
        # _logger.warning('failed to get svc up device')
        return '', {'x': 0, 'y': 0, 'angle': 0}

    # 获取地码
    def get_dmcode_sn(self, hardware_state):
        for device in list(hardware_state.devices):
            if device.id in (DeviceID.DOWN_SVC, DeviceID.DOWN_SVC_200):
                if device.info == '':
                    break
                sn, x, y, angle = self.parse_dmcode_info(device.info)
                return sn, {'x': x, 'y': y, 'angle': angle}
        return '', {'x': 0, 'y': 0, 'angle': 0}

    def get_current_dmcode_angle(self):
        _, last_pose = self.get_dmcode_sn(self._hardware_state)
        _logger.info(f'dmcode angle {last_pose["angle"]}')
        return last_pose['angle']

    def get_battery_info(self):
        # 没有连接上sros时，也返回值，以便机器人在系统上能上线
        if self._hardware_state is None:
            status = main_pb2.HardwareState.BatteryState.BATTERY_NO_CHARGING
            percent = 80
            temperature = 30
            current = 5
            voltage = 10
            capacity = 100
            cycle_time = 10
        else:
            status = self._hardware_state.battery_state
            percent = self._hardware_state.battery_percentage
            temperature = round(self._hardware_state.battery_temperature * 10)
            current = round(self._hardware_state.battery_current / 100)
            voltage = round(self._hardware_state.battery_voltage / 10)
            capacity = self._hardware_state.battery_nominal_capacity / 1000
            cycle_time = self._hardware_state.battery_use_cycles
        return {
            'percent': percent,
            'temperature': temperature,
            'current': current,
            'voltage': voltage,
            'status': status,
            'capacity': int(capacity),
            'cycle_times': cycle_time,
        }

    # 单位mm
    def get_linear_velocity(self):
        if self._system_state is None:
            return 0
        return self._system_state.mc_state.v_x

    # 单位度 * 1000
    def get_angle_velocity(self):
        if self._system_state is None:
            return 0
        rad = self._system_state.mc_state.w / 1000.0
        return int(math.degrees(rad) * 1000)

    def set_sros_pose(self, pose, **kwargs):
        self._srp.set_sros_pose(pose, **kwargs)

    def set_hw_state(self, **kwargs):
        self._srp.set_hw_state(**kwargs)

    # 长度单位mm，角度单位(角度 * 1000)
    def get_cur_pose(self):
        if self._system_state is None:
            _logger.warning('system state is None, may not not connect to sros')
            return {'x': 0, 'y': 0, 'angle': 0}
        else:
            # 更新当前位置
            pose = self._system_state.location_pose
            radius = pose.yaw / 1000.0
            degree = AngleUtils.normalize_180(math.degrees(radius))

            # x/y单位mm
            return {'x': pose.x, 'y': pose.y, 'angle': int(degree * 1000)}

    def get_cur_angle(self):
        cur_pose = self.get_cur_pose()
        cur_angle = cur_pose['angle'] / 1000
        return AngleUtils.normalize_360(cur_angle)

    def parse_dmcode_info(self, text):
        # text = "T18678632(0.2mm, -0.3mm, 0.1°)"
        pattern = (
            r'\s*(\w+)\s*'
            r'\(\s*((\-)?\d+(\.\d+)?)m*\s*,\s*((\-)?\d+(\.\d+)?)m*\s*,\s*((\-)?\d+(\.\d+)?).*\s*\)'
        )

        result = re.match(pattern, text)
        if result is None:  # 可能不带偏移信息，仅货架码，原样返回，其他当作 0 处理
            _logger.info(f'text to parse: `{text}`, plain dmcode without offset info?')
            return text, 0, 0, 0
        dmcode, x, y, yaw = result.group(1), result.group(2), result.group(5), result.group(8)
        return (
            dmcode,
            round(float(x)) if x else 0,
            round(float(y)) if y else 0,
            float(yaw) if yaw else 0,
        )


if __name__ == '__main__':
    mock = True
    if mock:
        srp_wrapper = SrpWrapper(mock=True)
        srp_wrapper.login('127.0.0.1', 'admin', 'admin')
    else:
        srp_wrapper = SrpWrapper()
        srp_wrapper.login('10.10.68.15', 'admin', 'admin')
    srp_wrapper.sync_robot_state()
    keys = [ConfigKey.SERVER_IP]
    print(srp_wrapper.get_sros_configs(keys))
    time.sleep(1)
