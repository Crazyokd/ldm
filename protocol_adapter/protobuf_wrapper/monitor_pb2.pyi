from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Header(_message.Message):
    __slots__ = ["nick_name", "serial_number", "start_timestamp"]
    NICK_NAME_FIELD_NUMBER: _ClassVar[int]
    SERIAL_NUMBER_FIELD_NUMBER: _ClassVar[int]
    START_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    nick_name: str
    serial_number: str
    start_timestamp: int
    def __init__(self, nick_name: _Optional[str] = ..., serial_number: _Optional[str] = ..., start_timestamp: _Optional[int] = ...) -> None: ...

class Record(_message.Message):
    __slots__ = ["timestamp", "system_hardware", "module_state", "hardware_state", "location_data", "movement_data", "reserved_data", "system_statistics"]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_HARDWARE_FIELD_NUMBER: _ClassVar[int]
    MODULE_STATE_FIELD_NUMBER: _ClassVar[int]
    HARDWARE_STATE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_DATA_FIELD_NUMBER: _ClassVar[int]
    MOVEMENT_DATA_FIELD_NUMBER: _ClassVar[int]
    RESERVED_DATA_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_STATISTICS_FIELD_NUMBER: _ClassVar[int]
    timestamp: int
    system_hardware: SystemHardware
    module_state: ModuleState
    hardware_state: HardwareState
    location_data: LocationData
    movement_data: MovementData
    reserved_data: ReservedData
    system_statistics: SystemStatistics
    def __init__(self, timestamp: _Optional[int] = ..., system_hardware: _Optional[_Union[SystemHardware, _Mapping]] = ..., module_state: _Optional[_Union[ModuleState, _Mapping]] = ..., hardware_state: _Optional[_Union[HardwareState, _Mapping]] = ..., location_data: _Optional[_Union[LocationData, _Mapping]] = ..., movement_data: _Optional[_Union[MovementData, _Mapping]] = ..., reserved_data: _Optional[_Union[ReservedData, _Mapping]] = ..., system_statistics: _Optional[_Union[SystemStatistics, _Mapping]] = ...) -> None: ...

class SystemHardware(_message.Message):
    __slots__ = ["cpu_usage", "memory_usage", "disk_usage", "disk_remain_space", "cpu_temperature", "board_temperature", "self_memory_usage", "self_memory_used_space", "emmc_life_time", "emmc_pre_eol", "wireless_signal_wlan0", "network_ping_eth0", "network_ping_enp3s0", "network_eth0_pps", "network_eth0_bps", "network_eth0_rx_pps", "network_eth0_rx_bps", "network_eth0_tx_pps", "network_eth0_tx_bps", "network_enp3s0_rx_pps", "network_enp3s0_rx_bps", "network_enp3s0_tx_pps", "network_enp3s0_tx_bps", "network_can0_rx_pps", "network_can0_rx_bps", "network_can0_tx_pps", "network_can0_tx_bps"]
    class EmmcEolState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        EMMC_EOL_NA: _ClassVar[SystemHardware.EmmcEolState]
        EMMC_EOL_NORMAL: _ClassVar[SystemHardware.EmmcEolState]
        EMMC_EOL_WARNING: _ClassVar[SystemHardware.EmmcEolState]
        EMMC_EOL_URGENT: _ClassVar[SystemHardware.EmmcEolState]
    EMMC_EOL_NA: SystemHardware.EmmcEolState
    EMMC_EOL_NORMAL: SystemHardware.EmmcEolState
    EMMC_EOL_WARNING: SystemHardware.EmmcEolState
    EMMC_EOL_URGENT: SystemHardware.EmmcEolState
    CPU_USAGE_FIELD_NUMBER: _ClassVar[int]
    MEMORY_USAGE_FIELD_NUMBER: _ClassVar[int]
    DISK_USAGE_FIELD_NUMBER: _ClassVar[int]
    DISK_REMAIN_SPACE_FIELD_NUMBER: _ClassVar[int]
    CPU_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    BOARD_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    SELF_MEMORY_USAGE_FIELD_NUMBER: _ClassVar[int]
    SELF_MEMORY_USED_SPACE_FIELD_NUMBER: _ClassVar[int]
    EMMC_LIFE_TIME_FIELD_NUMBER: _ClassVar[int]
    EMMC_PRE_EOL_FIELD_NUMBER: _ClassVar[int]
    WIRELESS_SIGNAL_WLAN0_FIELD_NUMBER: _ClassVar[int]
    NETWORK_PING_ETH0_FIELD_NUMBER: _ClassVar[int]
    NETWORK_PING_ENP3S0_FIELD_NUMBER: _ClassVar[int]
    NETWORK_ETH0_PPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_ETH0_BPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_ETH0_RX_PPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_ETH0_RX_BPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_ETH0_TX_PPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_ETH0_TX_BPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_ENP3S0_RX_PPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_ENP3S0_RX_BPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_ENP3S0_TX_PPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_ENP3S0_TX_BPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_CAN0_RX_PPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_CAN0_RX_BPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_CAN0_TX_PPS_FIELD_NUMBER: _ClassVar[int]
    NETWORK_CAN0_TX_BPS_FIELD_NUMBER: _ClassVar[int]
    cpu_usage: int
    memory_usage: int
    disk_usage: int
    disk_remain_space: int
    cpu_temperature: int
    board_temperature: int
    self_memory_usage: int
    self_memory_used_space: int
    emmc_life_time: int
    emmc_pre_eol: SystemHardware.EmmcEolState
    wireless_signal_wlan0: int
    network_ping_eth0: int
    network_ping_enp3s0: int
    network_eth0_pps: int
    network_eth0_bps: int
    network_eth0_rx_pps: int
    network_eth0_rx_bps: int
    network_eth0_tx_pps: int
    network_eth0_tx_bps: int
    network_enp3s0_rx_pps: int
    network_enp3s0_rx_bps: int
    network_enp3s0_tx_pps: int
    network_enp3s0_tx_bps: int
    network_can0_rx_pps: int
    network_can0_rx_bps: int
    network_can0_tx_pps: int
    network_can0_tx_bps: int
    def __init__(self, cpu_usage: _Optional[int] = ..., memory_usage: _Optional[int] = ..., disk_usage: _Optional[int] = ..., disk_remain_space: _Optional[int] = ..., cpu_temperature: _Optional[int] = ..., board_temperature: _Optional[int] = ..., self_memory_usage: _Optional[int] = ..., self_memory_used_space: _Optional[int] = ..., emmc_life_time: _Optional[int] = ..., emmc_pre_eol: _Optional[_Union[SystemHardware.EmmcEolState, str]] = ..., wireless_signal_wlan0: _Optional[int] = ..., network_ping_eth0: _Optional[int] = ..., network_ping_enp3s0: _Optional[int] = ..., network_eth0_pps: _Optional[int] = ..., network_eth0_bps: _Optional[int] = ..., network_eth0_rx_pps: _Optional[int] = ..., network_eth0_rx_bps: _Optional[int] = ..., network_eth0_tx_pps: _Optional[int] = ..., network_eth0_tx_bps: _Optional[int] = ..., network_enp3s0_rx_pps: _Optional[int] = ..., network_enp3s0_rx_bps: _Optional[int] = ..., network_enp3s0_tx_pps: _Optional[int] = ..., network_enp3s0_tx_bps: _Optional[int] = ..., network_can0_rx_pps: _Optional[int] = ..., network_can0_rx_bps: _Optional[int] = ..., network_can0_tx_pps: _Optional[int] = ..., network_can0_tx_bps: _Optional[int] = ...) -> None: ...

class ModuleState(_message.Message):
    __slots__ = ["module_ping_main", "module_ping_network", "module_ping_navigaton", "module_ping_slam", "module_ping_location", "module_ping_monitor"]
    MODULE_PING_MAIN_FIELD_NUMBER: _ClassVar[int]
    MODULE_PING_NETWORK_FIELD_NUMBER: _ClassVar[int]
    MODULE_PING_NAVIGATON_FIELD_NUMBER: _ClassVar[int]
    MODULE_PING_SLAM_FIELD_NUMBER: _ClassVar[int]
    MODULE_PING_LOCATION_FIELD_NUMBER: _ClassVar[int]
    MODULE_PING_MONITOR_FIELD_NUMBER: _ClassVar[int]
    module_ping_main: int
    module_ping_network: int
    module_ping_navigaton: int
    module_ping_slam: int
    module_ping_location: int
    module_ping_monitor: int
    def __init__(self, module_ping_main: _Optional[int] = ..., module_ping_network: _Optional[int] = ..., module_ping_navigaton: _Optional[int] = ..., module_ping_slam: _Optional[int] = ..., module_ping_location: _Optional[int] = ..., module_ping_monitor: _Optional[int] = ...) -> None: ...

class PowerData(_message.Message):
    __slots__ = ["voltage", "current", "power"]
    VOLTAGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_FIELD_NUMBER: _ClassVar[int]
    POWER_FIELD_NUMBER: _ClassVar[int]
    voltage: int
    current: int
    power: int
    def __init__(self, voltage: _Optional[int] = ..., current: _Optional[int] = ..., power: _Optional[int] = ...) -> None: ...

class PowerSourceBU(_message.Message):
    __slots__ = ["cu_and_depth_camera", "usb", "brake", "front_lidar", "back_lidar", "speaker", "color_leds", "power_module", "main_controller"]
    CU_AND_DEPTH_CAMERA_FIELD_NUMBER: _ClassVar[int]
    USB_FIELD_NUMBER: _ClassVar[int]
    BRAKE_FIELD_NUMBER: _ClassVar[int]
    FRONT_LIDAR_FIELD_NUMBER: _ClassVar[int]
    BACK_LIDAR_FIELD_NUMBER: _ClassVar[int]
    SPEAKER_FIELD_NUMBER: _ClassVar[int]
    COLOR_LEDS_FIELD_NUMBER: _ClassVar[int]
    POWER_MODULE_FIELD_NUMBER: _ClassVar[int]
    MAIN_CONTROLLER_FIELD_NUMBER: _ClassVar[int]
    cu_and_depth_camera: PowerData
    usb: PowerData
    brake: PowerData
    front_lidar: PowerData
    back_lidar: PowerData
    speaker: PowerData
    color_leds: PowerData
    power_module: PowerData
    main_controller: PowerData
    def __init__(self, cu_and_depth_camera: _Optional[_Union[PowerData, _Mapping]] = ..., usb: _Optional[_Union[PowerData, _Mapping]] = ..., brake: _Optional[_Union[PowerData, _Mapping]] = ..., front_lidar: _Optional[_Union[PowerData, _Mapping]] = ..., back_lidar: _Optional[_Union[PowerData, _Mapping]] = ..., speaker: _Optional[_Union[PowerData, _Mapping]] = ..., color_leds: _Optional[_Union[PowerData, _Mapping]] = ..., power_module: _Optional[_Union[PowerData, _Mapping]] = ..., main_controller: _Optional[_Union[PowerData, _Mapping]] = ...) -> None: ...

class PowerSourceECB(_message.Message):
    __slots__ = ["speaker_and_screen", "side_color_leds", "main_lidar", "router_and5g", "obstacle_lidars", "clearance_lamp", "wired_actuated_encoder_and_cib"]
    SPEAKER_AND_SCREEN_FIELD_NUMBER: _ClassVar[int]
    SIDE_COLOR_LEDS_FIELD_NUMBER: _ClassVar[int]
    MAIN_LIDAR_FIELD_NUMBER: _ClassVar[int]
    ROUTER_AND5G_FIELD_NUMBER: _ClassVar[int]
    OBSTACLE_LIDARS_FIELD_NUMBER: _ClassVar[int]
    CLEARANCE_LAMP_FIELD_NUMBER: _ClassVar[int]
    WIRED_ACTUATED_ENCODER_AND_CIB_FIELD_NUMBER: _ClassVar[int]
    speaker_and_screen: PowerData
    side_color_leds: PowerData
    main_lidar: PowerData
    router_and5g: PowerData
    obstacle_lidars: PowerData
    clearance_lamp: PowerData
    wired_actuated_encoder_and_cib: PowerData
    def __init__(self, speaker_and_screen: _Optional[_Union[PowerData, _Mapping]] = ..., side_color_leds: _Optional[_Union[PowerData, _Mapping]] = ..., main_lidar: _Optional[_Union[PowerData, _Mapping]] = ..., router_and5g: _Optional[_Union[PowerData, _Mapping]] = ..., obstacle_lidars: _Optional[_Union[PowerData, _Mapping]] = ..., clearance_lamp: _Optional[_Union[PowerData, _Mapping]] = ..., wired_actuated_encoder_and_cib: _Optional[_Union[PowerData, _Mapping]] = ...) -> None: ...

class HardwareState(_message.Message):
    __slots__ = ["battery_velotage", "battery_current", "battery_remain_percentage", "battery_temperature", "battery_power", "battery_remain_time", "body_temperature_sensor0", "ac_motor1", "ac_motor2", "mc_motor1", "mc_motor2", "power_type", "power_ecb", "power_bu"]
    class PowerSourceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        POWER_SOURCE_NONE: _ClassVar[HardwareState.PowerSourceType]
        POWER_SOURCE_BU: _ClassVar[HardwareState.PowerSourceType]
        POWER_SOURCE_ECB: _ClassVar[HardwareState.PowerSourceType]
    POWER_SOURCE_NONE: HardwareState.PowerSourceType
    POWER_SOURCE_BU: HardwareState.PowerSourceType
    POWER_SOURCE_ECB: HardwareState.PowerSourceType
    BATTERY_VELOTAGE_FIELD_NUMBER: _ClassVar[int]
    BATTERY_CURRENT_FIELD_NUMBER: _ClassVar[int]
    BATTERY_REMAIN_PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    BATTERY_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    BATTERY_POWER_FIELD_NUMBER: _ClassVar[int]
    BATTERY_REMAIN_TIME_FIELD_NUMBER: _ClassVar[int]
    BODY_TEMPERATURE_SENSOR0_FIELD_NUMBER: _ClassVar[int]
    AC_MOTOR1_FIELD_NUMBER: _ClassVar[int]
    AC_MOTOR2_FIELD_NUMBER: _ClassVar[int]
    MC_MOTOR1_FIELD_NUMBER: _ClassVar[int]
    MC_MOTOR2_FIELD_NUMBER: _ClassVar[int]
    POWER_TYPE_FIELD_NUMBER: _ClassVar[int]
    POWER_ECB_FIELD_NUMBER: _ClassVar[int]
    POWER_BU_FIELD_NUMBER: _ClassVar[int]
    battery_velotage: int
    battery_current: int
    battery_remain_percentage: int
    battery_temperature: int
    battery_power: int
    battery_remain_time: int
    body_temperature_sensor0: int
    ac_motor1: PowerData
    ac_motor2: PowerData
    mc_motor1: PowerData
    mc_motor2: PowerData
    power_type: HardwareState.PowerSourceType
    power_ecb: PowerSourceECB
    power_bu: PowerSourceBU
    def __init__(self, battery_velotage: _Optional[int] = ..., battery_current: _Optional[int] = ..., battery_remain_percentage: _Optional[int] = ..., battery_temperature: _Optional[int] = ..., battery_power: _Optional[int] = ..., battery_remain_time: _Optional[int] = ..., body_temperature_sensor0: _Optional[int] = ..., ac_motor1: _Optional[_Union[PowerData, _Mapping]] = ..., ac_motor2: _Optional[_Union[PowerData, _Mapping]] = ..., mc_motor1: _Optional[_Union[PowerData, _Mapping]] = ..., mc_motor2: _Optional[_Union[PowerData, _Mapping]] = ..., power_type: _Optional[_Union[HardwareState.PowerSourceType, str]] = ..., power_ecb: _Optional[_Union[PowerSourceECB, _Mapping]] = ..., power_bu: _Optional[_Union[PowerSourceBU, _Mapping]] = ...) -> None: ...

class LocationData(_message.Message):
    __slots__ = ["x", "y", "confidence"]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    confidence: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ..., confidence: _Optional[int] = ...) -> None: ...

class ImuData(_message.Message):
    __slots__ = ["roll", "pitch", "yaw", "accelerated_velocity_x", "accelerated_velocity_y", "accelerated_velocity_z", "angular_velocity_x", "angular_velocity_y", "angular_velocity_z"]
    ROLL_FIELD_NUMBER: _ClassVar[int]
    PITCH_FIELD_NUMBER: _ClassVar[int]
    YAW_FIELD_NUMBER: _ClassVar[int]
    ACCELERATED_VELOCITY_X_FIELD_NUMBER: _ClassVar[int]
    ACCELERATED_VELOCITY_Y_FIELD_NUMBER: _ClassVar[int]
    ACCELERATED_VELOCITY_Z_FIELD_NUMBER: _ClassVar[int]
    ANGULAR_VELOCITY_X_FIELD_NUMBER: _ClassVar[int]
    ANGULAR_VELOCITY_Y_FIELD_NUMBER: _ClassVar[int]
    ANGULAR_VELOCITY_Z_FIELD_NUMBER: _ClassVar[int]
    roll: float
    pitch: float
    yaw: float
    accelerated_velocity_x: float
    accelerated_velocity_y: float
    accelerated_velocity_z: float
    angular_velocity_x: float
    angular_velocity_y: float
    angular_velocity_z: float
    def __init__(self, roll: _Optional[float] = ..., pitch: _Optional[float] = ..., yaw: _Optional[float] = ..., accelerated_velocity_x: _Optional[float] = ..., accelerated_velocity_y: _Optional[float] = ..., accelerated_velocity_z: _Optional[float] = ..., angular_velocity_x: _Optional[float] = ..., angular_velocity_y: _Optional[float] = ..., angular_velocity_z: _Optional[float] = ...) -> None: ...

class MovementData(_message.Message):
    __slots__ = ["actual_linear_velocity", "actual_angular_velocity", "dst_linear_velocity", "dst_angular_velocity", "imu_data_array", "ac_motor1_actual_rpm", "ac_motor2_actual_rpm", "mc_motor1_actual_rpm", "mc_motor2_actual_rpm"]
    ACTUAL_LINEAR_VELOCITY_FIELD_NUMBER: _ClassVar[int]
    ACTUAL_ANGULAR_VELOCITY_FIELD_NUMBER: _ClassVar[int]
    DST_LINEAR_VELOCITY_FIELD_NUMBER: _ClassVar[int]
    DST_ANGULAR_VELOCITY_FIELD_NUMBER: _ClassVar[int]
    IMU_DATA_ARRAY_FIELD_NUMBER: _ClassVar[int]
    AC_MOTOR1_ACTUAL_RPM_FIELD_NUMBER: _ClassVar[int]
    AC_MOTOR2_ACTUAL_RPM_FIELD_NUMBER: _ClassVar[int]
    MC_MOTOR1_ACTUAL_RPM_FIELD_NUMBER: _ClassVar[int]
    MC_MOTOR2_ACTUAL_RPM_FIELD_NUMBER: _ClassVar[int]
    actual_linear_velocity: int
    actual_angular_velocity: int
    dst_linear_velocity: int
    dst_angular_velocity: int
    imu_data_array: _containers.RepeatedCompositeFieldContainer[ImuData]
    ac_motor1_actual_rpm: float
    ac_motor2_actual_rpm: float
    mc_motor1_actual_rpm: float
    mc_motor2_actual_rpm: float
    def __init__(self, actual_linear_velocity: _Optional[int] = ..., actual_angular_velocity: _Optional[int] = ..., dst_linear_velocity: _Optional[int] = ..., dst_angular_velocity: _Optional[int] = ..., imu_data_array: _Optional[_Iterable[_Union[ImuData, _Mapping]]] = ..., ac_motor1_actual_rpm: _Optional[float] = ..., ac_motor2_actual_rpm: _Optional[float] = ..., mc_motor1_actual_rpm: _Optional[float] = ..., mc_motor2_actual_rpm: _Optional[float] = ...) -> None: ...

class SystemStatistics(_message.Message):
    __slots__ = ["lidar_obstacle_avoidance_count", "depth_camera_obstacle_avoidance_count", "tof_obstacle_avoidance_count", "brake_unlocked_count", "auto_charge_count", "screen_touched_count", "total_power_cycle_count", "emergency_stop_triggers_count", "emergency_stop_triggers_errorcode", "other_exception_count", "other_exception_errorcode"]
    LIDAR_OBSTACLE_AVOIDANCE_COUNT_FIELD_NUMBER: _ClassVar[int]
    DEPTH_CAMERA_OBSTACLE_AVOIDANCE_COUNT_FIELD_NUMBER: _ClassVar[int]
    TOF_OBSTACLE_AVOIDANCE_COUNT_FIELD_NUMBER: _ClassVar[int]
    BRAKE_UNLOCKED_COUNT_FIELD_NUMBER: _ClassVar[int]
    AUTO_CHARGE_COUNT_FIELD_NUMBER: _ClassVar[int]
    SCREEN_TOUCHED_COUNT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_POWER_CYCLE_COUNT_FIELD_NUMBER: _ClassVar[int]
    EMERGENCY_STOP_TRIGGERS_COUNT_FIELD_NUMBER: _ClassVar[int]
    EMERGENCY_STOP_TRIGGERS_ERRORCODE_FIELD_NUMBER: _ClassVar[int]
    OTHER_EXCEPTION_COUNT_FIELD_NUMBER: _ClassVar[int]
    OTHER_EXCEPTION_ERRORCODE_FIELD_NUMBER: _ClassVar[int]
    lidar_obstacle_avoidance_count: int
    depth_camera_obstacle_avoidance_count: int
    tof_obstacle_avoidance_count: int
    brake_unlocked_count: int
    auto_charge_count: int
    screen_touched_count: int
    total_power_cycle_count: int
    emergency_stop_triggers_count: int
    emergency_stop_triggers_errorcode: _containers.RepeatedScalarFieldContainer[int]
    other_exception_count: int
    other_exception_errorcode: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, lidar_obstacle_avoidance_count: _Optional[int] = ..., depth_camera_obstacle_avoidance_count: _Optional[int] = ..., tof_obstacle_avoidance_count: _Optional[int] = ..., brake_unlocked_count: _Optional[int] = ..., auto_charge_count: _Optional[int] = ..., screen_touched_count: _Optional[int] = ..., total_power_cycle_count: _Optional[int] = ..., emergency_stop_triggers_count: _Optional[int] = ..., emergency_stop_triggers_errorcode: _Optional[_Iterable[int]] = ..., other_exception_count: _Optional[int] = ..., other_exception_errorcode: _Optional[_Iterable[int]] = ...) -> None: ...

class ReservedData(_message.Message):
    __slots__ = ["int32_0", "int32_1", "int32_2", "int32_3", "double_0", "double_1", "double_2", "double_3", "string_0", "string_1", "string_2", "string_3"]
    INT32_0_FIELD_NUMBER: _ClassVar[int]
    INT32_1_FIELD_NUMBER: _ClassVar[int]
    INT32_2_FIELD_NUMBER: _ClassVar[int]
    INT32_3_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_0_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_1_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_2_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_3_FIELD_NUMBER: _ClassVar[int]
    STRING_0_FIELD_NUMBER: _ClassVar[int]
    STRING_1_FIELD_NUMBER: _ClassVar[int]
    STRING_2_FIELD_NUMBER: _ClassVar[int]
    STRING_3_FIELD_NUMBER: _ClassVar[int]
    int32_0: int
    int32_1: int
    int32_2: int
    int32_3: int
    double_0: float
    double_1: float
    double_2: float
    double_3: float
    string_0: str
    string_1: str
    string_2: str
    string_3: str
    def __init__(self, int32_0: _Optional[int] = ..., int32_1: _Optional[int] = ..., int32_2: _Optional[int] = ..., int32_3: _Optional[int] = ..., double_0: _Optional[float] = ..., double_1: _Optional[float] = ..., double_2: _Optional[float] = ..., double_3: _Optional[float] = ..., string_0: _Optional[str] = ..., string_1: _Optional[str] = ..., string_2: _Optional[str] = ..., string_3: _Optional[str] = ...) -> None: ...

class VibrationSensor(_message.Message):
    __slots__ = ["timestamp_us", "x_ac_g", "y_ac_g", "z_ac_g"]
    TIMESTAMP_US_FIELD_NUMBER: _ClassVar[int]
    X_AC_G_FIELD_NUMBER: _ClassVar[int]
    Y_AC_G_FIELD_NUMBER: _ClassVar[int]
    Z_AC_G_FIELD_NUMBER: _ClassVar[int]
    timestamp_us: int
    x_ac_g: float
    y_ac_g: float
    z_ac_g: float
    def __init__(self, timestamp_us: _Optional[int] = ..., x_ac_g: _Optional[float] = ..., y_ac_g: _Optional[float] = ..., z_ac_g: _Optional[float] = ...) -> None: ...

class MotorSensor(_message.Message):
    __slots__ = ["timestamp_us", "speed_rpm", "current_A", "voltage_V", "temperature_C"]
    TIMESTAMP_US_FIELD_NUMBER: _ClassVar[int]
    SPEED_RPM_FIELD_NUMBER: _ClassVar[int]
    CURRENT_A_FIELD_NUMBER: _ClassVar[int]
    VOLTAGE_V_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_C_FIELD_NUMBER: _ClassVar[int]
    timestamp_us: int
    speed_rpm: float
    current_A: float
    voltage_V: float
    temperature_C: float
    def __init__(self, timestamp_us: _Optional[int] = ..., speed_rpm: _Optional[float] = ..., current_A: _Optional[float] = ..., voltage_V: _Optional[float] = ..., temperature_C: _Optional[float] = ...) -> None: ...

class NoiseSensor(_message.Message):
    __slots__ = ["timestamp_us", "noise_db"]
    TIMESTAMP_US_FIELD_NUMBER: _ClassVar[int]
    NOISE_DB_FIELD_NUMBER: _ClassVar[int]
    timestamp_us: int
    noise_db: float
    def __init__(self, timestamp_us: _Optional[int] = ..., noise_db: _Optional[float] = ...) -> None: ...

class LoadUnitSensor(_message.Message):
    __slots__ = ["timestamp_us", "offset_m", "weight_kg", "angle_rad"]
    TIMESTAMP_US_FIELD_NUMBER: _ClassVar[int]
    OFFSET_M_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_KG_FIELD_NUMBER: _ClassVar[int]
    ANGLE_RAD_FIELD_NUMBER: _ClassVar[int]
    timestamp_us: int
    offset_m: float
    weight_kg: float
    angle_rad: float
    def __init__(self, timestamp_us: _Optional[int] = ..., offset_m: _Optional[float] = ..., weight_kg: _Optional[float] = ..., angle_rad: _Optional[float] = ...) -> None: ...

class Laser2DSensor(_message.Message):
    __slots__ = ["timestamp_us", "direction", "laser_type", "angle_range_deg", "sample_num", "resolution", "theta_deg", "x_mm", "y_mm", "z_mm", "data"]
    class Point(_message.Message):
        __slots__ = ["intensity", "distance_mm"]
        INTENSITY_FIELD_NUMBER: _ClassVar[int]
        DISTANCE_MM_FIELD_NUMBER: _ClassVar[int]
        intensity: int
        distance_mm: int
        def __init__(self, intensity: _Optional[int] = ..., distance_mm: _Optional[int] = ...) -> None: ...
    TIMESTAMP_US_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    LASER_TYPE_FIELD_NUMBER: _ClassVar[int]
    ANGLE_RANGE_DEG_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_NUM_FIELD_NUMBER: _ClassVar[int]
    RESOLUTION_FIELD_NUMBER: _ClassVar[int]
    THETA_DEG_FIELD_NUMBER: _ClassVar[int]
    X_MM_FIELD_NUMBER: _ClassVar[int]
    Y_MM_FIELD_NUMBER: _ClassVar[int]
    Z_MM_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    timestamp_us: int
    direction: int
    laser_type: int
    angle_range_deg: float
    sample_num: int
    resolution: int
    theta_deg: float
    x_mm: int
    y_mm: int
    z_mm: int
    data: _containers.RepeatedCompositeFieldContainer[Laser2DSensor.Point]
    def __init__(self, timestamp_us: _Optional[int] = ..., direction: _Optional[int] = ..., laser_type: _Optional[int] = ..., angle_range_deg: _Optional[float] = ..., sample_num: _Optional[int] = ..., resolution: _Optional[int] = ..., theta_deg: _Optional[float] = ..., x_mm: _Optional[int] = ..., y_mm: _Optional[int] = ..., z_mm: _Optional[int] = ..., data: _Optional[_Iterable[_Union[Laser2DSensor.Point, _Mapping]]] = ...) -> None: ...

class Laser3DSensor(_message.Message):
    __slots__ = ["timestamp_us", "direction", "laser_type", "h_angle_range_deg", "v_angle_range_deg", "h_angle_deg", "v_angle_deg", "sample_num", "x_mm", "y_mm", "z_mm", "data"]
    class Point(_message.Message):
        __slots__ = ["intensity", "x_mm", "y_mm", "z_mm"]
        INTENSITY_FIELD_NUMBER: _ClassVar[int]
        X_MM_FIELD_NUMBER: _ClassVar[int]
        Y_MM_FIELD_NUMBER: _ClassVar[int]
        Z_MM_FIELD_NUMBER: _ClassVar[int]
        intensity: int
        x_mm: int
        y_mm: int
        z_mm: int
        def __init__(self, intensity: _Optional[int] = ..., x_mm: _Optional[int] = ..., y_mm: _Optional[int] = ..., z_mm: _Optional[int] = ...) -> None: ...
    TIMESTAMP_US_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    LASER_TYPE_FIELD_NUMBER: _ClassVar[int]
    H_ANGLE_RANGE_DEG_FIELD_NUMBER: _ClassVar[int]
    V_ANGLE_RANGE_DEG_FIELD_NUMBER: _ClassVar[int]
    H_ANGLE_DEG_FIELD_NUMBER: _ClassVar[int]
    V_ANGLE_DEG_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_NUM_FIELD_NUMBER: _ClassVar[int]
    X_MM_FIELD_NUMBER: _ClassVar[int]
    Y_MM_FIELD_NUMBER: _ClassVar[int]
    Z_MM_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    timestamp_us: int
    direction: int
    laser_type: int
    h_angle_range_deg: float
    v_angle_range_deg: float
    h_angle_deg: float
    v_angle_deg: float
    sample_num: int
    x_mm: int
    y_mm: int
    z_mm: int
    data: _containers.RepeatedCompositeFieldContainer[Laser3DSensor.Point]
    def __init__(self, timestamp_us: _Optional[int] = ..., direction: _Optional[int] = ..., laser_type: _Optional[int] = ..., h_angle_range_deg: _Optional[float] = ..., v_angle_range_deg: _Optional[float] = ..., h_angle_deg: _Optional[float] = ..., v_angle_deg: _Optional[float] = ..., sample_num: _Optional[int] = ..., x_mm: _Optional[int] = ..., y_mm: _Optional[int] = ..., z_mm: _Optional[int] = ..., data: _Optional[_Iterable[_Union[Laser3DSensor.Point, _Mapping]]] = ...) -> None: ...

class EncoderSensor(_message.Message):
    __slots__ = ["timestamp_us", "v"]
    TIMESTAMP_US_FIELD_NUMBER: _ClassVar[int]
    V_FIELD_NUMBER: _ClassVar[int]
    timestamp_us: int
    v: int
    def __init__(self, timestamp_us: _Optional[int] = ..., v: _Optional[int] = ...) -> None: ...

class SensorDataCollection(_message.Message):
    __slots__ = ["vibration_1", "loadunit_1", "noise_1", "motor_lift", "motor_rotate", "motor_left", "motor_right", "lidar2d_front", "lidar2d_back", "lidar3d_front", "lidar3d_back", "encoder_lift", "encoder_rotate", "encoder_left", "encoder_right", "encoder_fork_front_back", "encoder_fork_left_right", "encoder_fork_height", "gpio_input", "gpio_output"]
    VIBRATION_1_FIELD_NUMBER: _ClassVar[int]
    LOADUNIT_1_FIELD_NUMBER: _ClassVar[int]
    NOISE_1_FIELD_NUMBER: _ClassVar[int]
    MOTOR_LIFT_FIELD_NUMBER: _ClassVar[int]
    MOTOR_ROTATE_FIELD_NUMBER: _ClassVar[int]
    MOTOR_LEFT_FIELD_NUMBER: _ClassVar[int]
    MOTOR_RIGHT_FIELD_NUMBER: _ClassVar[int]
    LIDAR2D_FRONT_FIELD_NUMBER: _ClassVar[int]
    LIDAR2D_BACK_FIELD_NUMBER: _ClassVar[int]
    LIDAR3D_FRONT_FIELD_NUMBER: _ClassVar[int]
    LIDAR3D_BACK_FIELD_NUMBER: _ClassVar[int]
    ENCODER_LIFT_FIELD_NUMBER: _ClassVar[int]
    ENCODER_ROTATE_FIELD_NUMBER: _ClassVar[int]
    ENCODER_LEFT_FIELD_NUMBER: _ClassVar[int]
    ENCODER_RIGHT_FIELD_NUMBER: _ClassVar[int]
    ENCODER_FORK_FRONT_BACK_FIELD_NUMBER: _ClassVar[int]
    ENCODER_FORK_LEFT_RIGHT_FIELD_NUMBER: _ClassVar[int]
    ENCODER_FORK_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    GPIO_INPUT_FIELD_NUMBER: _ClassVar[int]
    GPIO_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    vibration_1: _containers.RepeatedCompositeFieldContainer[VibrationSensor]
    loadunit_1: _containers.RepeatedCompositeFieldContainer[LoadUnitSensor]
    noise_1: _containers.RepeatedCompositeFieldContainer[NoiseSensor]
    motor_lift: _containers.RepeatedCompositeFieldContainer[MotorSensor]
    motor_rotate: _containers.RepeatedCompositeFieldContainer[MotorSensor]
    motor_left: _containers.RepeatedCompositeFieldContainer[MotorSensor]
    motor_right: _containers.RepeatedCompositeFieldContainer[MotorSensor]
    lidar2d_front: _containers.RepeatedCompositeFieldContainer[Laser2DSensor]
    lidar2d_back: _containers.RepeatedCompositeFieldContainer[Laser2DSensor]
    lidar3d_front: _containers.RepeatedCompositeFieldContainer[Laser3DSensor]
    lidar3d_back: _containers.RepeatedCompositeFieldContainer[Laser3DSensor]
    encoder_lift: _containers.RepeatedCompositeFieldContainer[EncoderSensor]
    encoder_rotate: _containers.RepeatedCompositeFieldContainer[EncoderSensor]
    encoder_left: _containers.RepeatedCompositeFieldContainer[EncoderSensor]
    encoder_right: _containers.RepeatedCompositeFieldContainer[EncoderSensor]
    encoder_fork_front_back: _containers.RepeatedCompositeFieldContainer[EncoderSensor]
    encoder_fork_left_right: _containers.RepeatedCompositeFieldContainer[EncoderSensor]
    encoder_fork_height: _containers.RepeatedCompositeFieldContainer[EncoderSensor]
    gpio_input: int
    gpio_output: int
    def __init__(self, vibration_1: _Optional[_Iterable[_Union[VibrationSensor, _Mapping]]] = ..., loadunit_1: _Optional[_Iterable[_Union[LoadUnitSensor, _Mapping]]] = ..., noise_1: _Optional[_Iterable[_Union[NoiseSensor, _Mapping]]] = ..., motor_lift: _Optional[_Iterable[_Union[MotorSensor, _Mapping]]] = ..., motor_rotate: _Optional[_Iterable[_Union[MotorSensor, _Mapping]]] = ..., motor_left: _Optional[_Iterable[_Union[MotorSensor, _Mapping]]] = ..., motor_right: _Optional[_Iterable[_Union[MotorSensor, _Mapping]]] = ..., lidar2d_front: _Optional[_Iterable[_Union[Laser2DSensor, _Mapping]]] = ..., lidar2d_back: _Optional[_Iterable[_Union[Laser2DSensor, _Mapping]]] = ..., lidar3d_front: _Optional[_Iterable[_Union[Laser3DSensor, _Mapping]]] = ..., lidar3d_back: _Optional[_Iterable[_Union[Laser3DSensor, _Mapping]]] = ..., encoder_lift: _Optional[_Iterable[_Union[EncoderSensor, _Mapping]]] = ..., encoder_rotate: _Optional[_Iterable[_Union[EncoderSensor, _Mapping]]] = ..., encoder_left: _Optional[_Iterable[_Union[EncoderSensor, _Mapping]]] = ..., encoder_right: _Optional[_Iterable[_Union[EncoderSensor, _Mapping]]] = ..., encoder_fork_front_back: _Optional[_Iterable[_Union[EncoderSensor, _Mapping]]] = ..., encoder_fork_left_right: _Optional[_Iterable[_Union[EncoderSensor, _Mapping]]] = ..., encoder_fork_height: _Optional[_Iterable[_Union[EncoderSensor, _Mapping]]] = ..., gpio_input: _Optional[int] = ..., gpio_output: _Optional[int] = ...) -> None: ...
