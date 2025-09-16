from protocol_adapter.protobuf_wrapper import monitor_pb2 as _monitor_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    MSG_REQUEST: _ClassVar[MessageType]
    MSG_RESPONSE: _ClassVar[MessageType]
    MSG_COMMAND: _ClassVar[MessageType]
    MSG_NOTIFICATION: _ClassVar[MessageType]

class CommandType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    CMD_ZERO: _ClassVar[CommandType]
    CMD_START_LOCATION: _ClassVar[CommandType]
    CMD_STOP_LOCATION: _ClassVar[CommandType]
    CMD_PAUSE_MOVEMENT: _ClassVar[CommandType]
    CMD_CONTINUE_MOVEMENT: _ClassVar[CommandType]
    CMD_STOP_MOVEMENT: _ClassVar[CommandType]
    CMD_ENABLE_MANUAL_CONTROL: _ClassVar[CommandType]
    CMD_DISABLE_MANUAL_CONTROL: _ClassVar[CommandType]
    CMD_SRC_RESET: _ClassVar[CommandType]
    CMD_SET_SPEED_LEVEL: _ClassVar[CommandType]
    CMD_SET_CUR_MAP: _ClassVar[CommandType]
    CMD_SET_CUR_STATION: _ClassVar[CommandType]
    CMD_MAP_SWITCHING: _ClassVar[CommandType]
    CMD_ENABLE_OBSTACLE_AVOID: _ClassVar[CommandType]
    CMD_DISABLE_OBSTACLE_AVOID: _ClassVar[CommandType]
    CMD_STOP_SROS: _ClassVar[CommandType]
    CMD_RESET_SRP: _ClassVar[CommandType]
    CMD_SET_MANUAL_SPEED: _ClassVar[CommandType]
    CMD_ACTION_TASK: _ClassVar[CommandType]
    CMD_CANCEL_EMERGENCY: _ClassVar[CommandType]
    CMD_ENABLE_AUTO_CHARGE: _ClassVar[CommandType]
    CMD_NEW_MAP_START: _ClassVar[CommandType]
    CMD_NEW_MAP_STOP: _ClassVar[CommandType]
    CMD_NEW_MAP_CANCEL: _ClassVar[CommandType]
    CMD_SET_LOCATION_INITIAL_POSE: _ClassVar[CommandType]
    CMD_SYNC_TIME: _ClassVar[CommandType]
    CMD_COMMON_CANCEL: _ClassVar[CommandType]
    CMD_LOCK_CONTROL_MUTEX: _ClassVar[CommandType]
    CMD_UNLOCK_CONTROL_MUTEX: _ClassVar[CommandType]
    CMD_FORCE_UNLOCK_CONTROL_MUTEX: _ClassVar[CommandType]
    CMD_NEW_MOVEMENT_TASK: _ClassVar[CommandType]
    CMD_CANCEL_MOVEMENT_TASK: _ClassVar[CommandType]
    CMD_SET_CHECKPOINT: _ClassVar[CommandType]
    CMD_PATH_REPLACE: _ClassVar[CommandType]
    CMD_NEW_ACTION_TASK: _ClassVar[CommandType]
    CMD_CANCEL_ACTION_TASK: _ClassVar[CommandType]
    CMD_SET_GENERAL_IO_OUTPUT: _ClassVar[CommandType]
    CMD_SET_SPEAKER_VOLUME: _ClassVar[CommandType]
    CMD_SET_HMI_STATE: _ClassVar[CommandType]
    CMD_SPEED_SLOW_DOWN: _ClassVar[CommandType]
    CMD_CALIBRATION: _ClassVar[CommandType]
    CMD_TRIGGER_EMERGENCY: _ClassVar[CommandType]
    CMD_ENABLE_AUTO_UPLOAD_LASER_POINT: _ClassVar[CommandType]
    CMD_DISABLE_AUTO_UPLOAD_LASER_POINT: _ClassVar[CommandType]
    CMD_RESET_FAULT: _ClassVar[CommandType]
    CMD_ENTER_POWER_SAVE_MODE: _ClassVar[CommandType]
    CMD_EXIT_POWER_SAVE_MODE: _ClassVar[CommandType]
    CMD_STOP_CHARGE: _ClassVar[CommandType]
    CMD_ENABLE_UPLOAD_AVOID_OBSTACLE_PREDICTION: _ClassVar[CommandType]
    CMD_DISABLE_UPLOAD_AVOID_OBSTACLE_PREDICTION: _ClassVar[CommandType]
    CMD_INPUT_ACTION_VALUE: _ClassVar[CommandType]
    CMD_START_MISSION: _ClassVar[CommandType]
    CMD_CANCEL_MISSION: _ClassVar[CommandType]
    CMD_CONTINUE_MISSION: _ClassVar[CommandType]
    CMD_REORDER_MISSION: _ClassVar[CommandType]
    CMD_ADD_PGV_INFO: _ClassVar[CommandType]
    CMD_DEL_PGV_INFO: _ClassVar[CommandType]
    CMD_APPEND_PATH: _ClassVar[CommandType]
    CMD_ENABLE_DEBUG_INFO: _ClassVar[CommandType]
    CMD_DISABLE_DEBUG_INFO: _ClassVar[CommandType]
    CMD_ENABLE_DEBUG_FEATURE: _ClassVar[CommandType]
    CMD_DISABLE_DEBUG_FEATURE: _ClassVar[CommandType]
    CMD_ENABLE_DEBUG_DISPLAY_IMAGES: _ClassVar[CommandType]
    CMD_DISABLE_DEBUG_DISPLAY_IMAGES: _ClassVar[CommandType]
    CMD_ENABLE_DEBUG_DATA: _ClassVar[CommandType]
    CMD_DISABLE_DEBUG_DATA: _ClassVar[CommandType]
    CMD_PLAY_MUSIC: _ClassVar[CommandType]
    CMD_PLAY_LIGHT: _ClassVar[CommandType]
    CMD_CALIBR_CAMERA: _ClassVar[CommandType]
    CMD_DEVICE_TESTING: _ClassVar[CommandType]
    CMD_CALIBR_IMU: _ClassVar[CommandType]
    CMD_REDRAW_START: _ClassVar[CommandType]
    CMD_REDRAW_STOP: _ClassVar[CommandType]
    CMD_REDRAW_CANCEL: _ClassVar[CommandType]
    CMD_REDRAW_STOP_CHECK: _ClassVar[CommandType]
    CMD_REDRAW_FINISH: _ClassVar[CommandType]
    CMD_ENABLE_MANUAL_CONTROL_OBA: _ClassVar[CommandType]
    CMD_DISABLE_MANUAL_CONTROL_OBA: _ClassVar[CommandType]
    CMD_SYSTEM_SHUTDOWN: _ClassVar[CommandType]
    CMD_SWITCH_LOAD_STATE: _ClassVar[CommandType]
    CMD_ENTER_CLEAN_WHEEL_MODE: _ClassVar[CommandType]
    CMD_EXIT_CLEAN_WHEEL_MODE: _ClassVar[CommandType]
    CMD_SET_SCHEDULING_MODE: _ClassVar[CommandType]
    CMD_CLEAR_LOCATION_UNCONFIRMED_STATE: _ClassVar[CommandType]
    CMD_NOTIFY_FMS_VERSION: _ClassVar[CommandType]

class TaskResult(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    TASK_RESULT_NA: _ClassVar[TaskResult]
    TASK_RESULT_OK: _ClassVar[TaskResult]
    TASK_RESULT_CANCELED: _ClassVar[TaskResult]
    TASK_RESULT_FAILED: _ClassVar[TaskResult]

class AvoidPolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    AT_ZERO: _ClassVar[AvoidPolicy]
    OBSTACLE_AVOID_WAIT: _ClassVar[AvoidPolicy]
    OBSTACLE_AVOID_REPLAN: _ClassVar[AvoidPolicy]
    OBSTACLE_AVOID_NONE: _ClassVar[AvoidPolicy]
MSG_REQUEST: MessageType
MSG_RESPONSE: MessageType
MSG_COMMAND: MessageType
MSG_NOTIFICATION: MessageType
CMD_ZERO: CommandType
CMD_START_LOCATION: CommandType
CMD_STOP_LOCATION: CommandType
CMD_PAUSE_MOVEMENT: CommandType
CMD_CONTINUE_MOVEMENT: CommandType
CMD_STOP_MOVEMENT: CommandType
CMD_ENABLE_MANUAL_CONTROL: CommandType
CMD_DISABLE_MANUAL_CONTROL: CommandType
CMD_SRC_RESET: CommandType
CMD_SET_SPEED_LEVEL: CommandType
CMD_SET_CUR_MAP: CommandType
CMD_SET_CUR_STATION: CommandType
CMD_MAP_SWITCHING: CommandType
CMD_ENABLE_OBSTACLE_AVOID: CommandType
CMD_DISABLE_OBSTACLE_AVOID: CommandType
CMD_STOP_SROS: CommandType
CMD_RESET_SRP: CommandType
CMD_SET_MANUAL_SPEED: CommandType
CMD_ACTION_TASK: CommandType
CMD_CANCEL_EMERGENCY: CommandType
CMD_ENABLE_AUTO_CHARGE: CommandType
CMD_NEW_MAP_START: CommandType
CMD_NEW_MAP_STOP: CommandType
CMD_NEW_MAP_CANCEL: CommandType
CMD_SET_LOCATION_INITIAL_POSE: CommandType
CMD_SYNC_TIME: CommandType
CMD_COMMON_CANCEL: CommandType
CMD_LOCK_CONTROL_MUTEX: CommandType
CMD_UNLOCK_CONTROL_MUTEX: CommandType
CMD_FORCE_UNLOCK_CONTROL_MUTEX: CommandType
CMD_NEW_MOVEMENT_TASK: CommandType
CMD_CANCEL_MOVEMENT_TASK: CommandType
CMD_SET_CHECKPOINT: CommandType
CMD_PATH_REPLACE: CommandType
CMD_NEW_ACTION_TASK: CommandType
CMD_CANCEL_ACTION_TASK: CommandType
CMD_SET_GENERAL_IO_OUTPUT: CommandType
CMD_SET_SPEAKER_VOLUME: CommandType
CMD_SET_HMI_STATE: CommandType
CMD_SPEED_SLOW_DOWN: CommandType
CMD_CALIBRATION: CommandType
CMD_TRIGGER_EMERGENCY: CommandType
CMD_ENABLE_AUTO_UPLOAD_LASER_POINT: CommandType
CMD_DISABLE_AUTO_UPLOAD_LASER_POINT: CommandType
CMD_RESET_FAULT: CommandType
CMD_ENTER_POWER_SAVE_MODE: CommandType
CMD_EXIT_POWER_SAVE_MODE: CommandType
CMD_STOP_CHARGE: CommandType
CMD_ENABLE_UPLOAD_AVOID_OBSTACLE_PREDICTION: CommandType
CMD_DISABLE_UPLOAD_AVOID_OBSTACLE_PREDICTION: CommandType
CMD_INPUT_ACTION_VALUE: CommandType
CMD_START_MISSION: CommandType
CMD_CANCEL_MISSION: CommandType
CMD_CONTINUE_MISSION: CommandType
CMD_REORDER_MISSION: CommandType
CMD_ADD_PGV_INFO: CommandType
CMD_DEL_PGV_INFO: CommandType
CMD_APPEND_PATH: CommandType
CMD_ENABLE_DEBUG_INFO: CommandType
CMD_DISABLE_DEBUG_INFO: CommandType
CMD_ENABLE_DEBUG_FEATURE: CommandType
CMD_DISABLE_DEBUG_FEATURE: CommandType
CMD_ENABLE_DEBUG_DISPLAY_IMAGES: CommandType
CMD_DISABLE_DEBUG_DISPLAY_IMAGES: CommandType
CMD_ENABLE_DEBUG_DATA: CommandType
CMD_DISABLE_DEBUG_DATA: CommandType
CMD_PLAY_MUSIC: CommandType
CMD_PLAY_LIGHT: CommandType
CMD_CALIBR_CAMERA: CommandType
CMD_DEVICE_TESTING: CommandType
CMD_CALIBR_IMU: CommandType
CMD_REDRAW_START: CommandType
CMD_REDRAW_STOP: CommandType
CMD_REDRAW_CANCEL: CommandType
CMD_REDRAW_STOP_CHECK: CommandType
CMD_REDRAW_FINISH: CommandType
CMD_ENABLE_MANUAL_CONTROL_OBA: CommandType
CMD_DISABLE_MANUAL_CONTROL_OBA: CommandType
CMD_SYSTEM_SHUTDOWN: CommandType
CMD_SWITCH_LOAD_STATE: CommandType
CMD_ENTER_CLEAN_WHEEL_MODE: CommandType
CMD_EXIT_CLEAN_WHEEL_MODE: CommandType
CMD_SET_SCHEDULING_MODE: CommandType
CMD_CLEAR_LOCATION_UNCONFIRMED_STATE: CommandType
CMD_NOTIFY_FMS_VERSION: CommandType
TASK_RESULT_NA: TaskResult
TASK_RESULT_OK: TaskResult
TASK_RESULT_CANCELED: TaskResult
TASK_RESULT_FAILED: TaskResult
AT_ZERO: AvoidPolicy
OBSTACLE_AVOID_WAIT: AvoidPolicy
OBSTACLE_AVOID_REPLAN: AvoidPolicy
OBSTACLE_AVOID_NONE: AvoidPolicy

class Message(_message.Message):
    __slots__ = ["type", "seq", "session_id", "request", "response", "command", "notification"]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SEQ_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_FIELD_NUMBER: _ClassVar[int]
    type: MessageType
    seq: int
    session_id: int
    request: Request
    response: Response
    command: Command
    notification: Notification
    def __init__(self, type: _Optional[_Union[MessageType, str]] = ..., seq: _Optional[int] = ..., session_id: _Optional[int] = ..., request: _Optional[_Union[Request, _Mapping]] = ..., response: _Optional[_Union[Response, _Mapping]] = ..., command: _Optional[_Union[Command, _Mapping]] = ..., notification: _Optional[_Union[Notification, _Mapping]] = ...) -> None: ...

class Request(_message.Message):
    __slots__ = ["request_type", "login_request", "file_op", "param_str", "param_str1", "param_str2", "param_int", "param_int1", "config", "tmp_configs", "redraw_polygon", "lock_unlock_area", "back_pose_in_net"]
    class RequestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        REQUEST_LOGIN: _ClassVar[Request.RequestType]
        REQUEST_INFO: _ClassVar[Request.RequestType]
        REQUEST_ALL_STATE: _ClassVar[Request.RequestType]
        REQUEST_SYSTEM_STATE: _ClassVar[Request.RequestType]
        REQUEST_HARDWARE_STATE: _ClassVar[Request.RequestType]
        REQUEST_MAP_LIST: _ClassVar[Request.RequestType]
        REQUEST_BAG_LIST: _ClassVar[Request.RequestType]
        REQUEST_LASER_POINTS: _ClassVar[Request.RequestType]
        REQUEST_TASK_STATE: _ClassVar[Request.RequestType]
        REQUEST_FILE_OPERATE: _ClassVar[Request.RequestType]
        REQUEST_LOGOUT: _ClassVar[Request.RequestType]
        REQUEST_LOAD_CONFIG: _ClassVar[Request.RequestType]
        REQUEST_SAVE_CONFIG: _ClassVar[Request.RequestType]
        REQUEST_LOAD_TMP_CONFIG: _ClassVar[Request.RequestType]
        REQUEST_SAVE_TMP_CONFIG: _ClassVar[Request.RequestType]
        REQUEST_FILE_LIST: _ClassVar[Request.RequestType]
        REQUEST_MONITOR_DATA: _ClassVar[Request.RequestType]
        REQUEST_CHANGE_PW: _ClassVar[Request.RequestType]
        REQUEST_TIMESTAMP: _ClassVar[Request.RequestType]
        REQUEST_GET_CUT_MAP: _ClassVar[Request.RequestType]
        REQUEST_MISSION_LIST: _ClassVar[Request.RequestType]
        REQUEST_HEARTBEAT: _ClassVar[Request.RequestType]
        REQUEST_CONNECT_INFO: _ClassVar[Request.RequestType]
        REQUEST_REDRAW_DATA: _ClassVar[Request.RequestType]
        REQUEST_SYSTEM_CMD: _ClassVar[Request.RequestType]
        REQUEST_LOCK_SPACE: _ClassVar[Request.RequestType]
        REQUEST_UNLOCK_SPACE: _ClassVar[Request.RequestType]
        REQUEST_BACK_TO_PATH: _ClassVar[Request.RequestType]
        REQUEST_SENSOR_SAMPLES: _ClassVar[Request.RequestType]
        REQUEST_READ_DISCRETE_INPUTS: _ClassVar[Request.RequestType]
        REQUEST_READ_COILS: _ClassVar[Request.RequestType]
        REQUEST_WRITE_SINGLE_COIL: _ClassVar[Request.RequestType]
        REQUEST_WRITE_MULTIPLE_COILS: _ClassVar[Request.RequestType]
        REQUEST_READ_INPUT_REGISTER: _ClassVar[Request.RequestType]
        REQUEST_READ_HOLDING_REGISTERS: _ClassVar[Request.RequestType]
        REQUEST_WRITE_SINGLE_REGISTER: _ClassVar[Request.RequestType]
        REQUEST_WRITE_MULTIPLE_REGISTERS: _ClassVar[Request.RequestType]
        REQUEST_READ_ALL_REGISTERS: _ClassVar[Request.RequestType]
        REQUEST_GET_CAMERA_PICTURE: _ClassVar[Request.RequestType]
    REQUEST_LOGIN: Request.RequestType
    REQUEST_INFO: Request.RequestType
    REQUEST_ALL_STATE: Request.RequestType
    REQUEST_SYSTEM_STATE: Request.RequestType
    REQUEST_HARDWARE_STATE: Request.RequestType
    REQUEST_MAP_LIST: Request.RequestType
    REQUEST_BAG_LIST: Request.RequestType
    REQUEST_LASER_POINTS: Request.RequestType
    REQUEST_TASK_STATE: Request.RequestType
    REQUEST_FILE_OPERATE: Request.RequestType
    REQUEST_LOGOUT: Request.RequestType
    REQUEST_LOAD_CONFIG: Request.RequestType
    REQUEST_SAVE_CONFIG: Request.RequestType
    REQUEST_LOAD_TMP_CONFIG: Request.RequestType
    REQUEST_SAVE_TMP_CONFIG: Request.RequestType
    REQUEST_FILE_LIST: Request.RequestType
    REQUEST_MONITOR_DATA: Request.RequestType
    REQUEST_CHANGE_PW: Request.RequestType
    REQUEST_TIMESTAMP: Request.RequestType
    REQUEST_GET_CUT_MAP: Request.RequestType
    REQUEST_MISSION_LIST: Request.RequestType
    REQUEST_HEARTBEAT: Request.RequestType
    REQUEST_CONNECT_INFO: Request.RequestType
    REQUEST_REDRAW_DATA: Request.RequestType
    REQUEST_SYSTEM_CMD: Request.RequestType
    REQUEST_LOCK_SPACE: Request.RequestType
    REQUEST_UNLOCK_SPACE: Request.RequestType
    REQUEST_BACK_TO_PATH: Request.RequestType
    REQUEST_SENSOR_SAMPLES: Request.RequestType
    REQUEST_READ_DISCRETE_INPUTS: Request.RequestType
    REQUEST_READ_COILS: Request.RequestType
    REQUEST_WRITE_SINGLE_COIL: Request.RequestType
    REQUEST_WRITE_MULTIPLE_COILS: Request.RequestType
    REQUEST_READ_INPUT_REGISTER: Request.RequestType
    REQUEST_READ_HOLDING_REGISTERS: Request.RequestType
    REQUEST_WRITE_SINGLE_REGISTER: Request.RequestType
    REQUEST_WRITE_MULTIPLE_REGISTERS: Request.RequestType
    REQUEST_READ_ALL_REGISTERS: Request.RequestType
    REQUEST_GET_CAMERA_PICTURE: Request.RequestType
    class FileOperateType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        FILE_OPERATE_ZERO: _ClassVar[Request.FileOperateType]
        GET_NAV_MAP_FILE: _ClassVar[Request.FileOperateType]
        SET_NAV_MAP_FILE: _ClassVar[Request.FileOperateType]
        GET_RAW_MAP_FILE: _ClassVar[Request.FileOperateType]
        SET_RAW_MAP_FILE: _ClassVar[Request.FileOperateType]
        EXPORT_MAP_FILE: _ClassVar[Request.FileOperateType]
        IMPORT_MAP_FILE: _ClassVar[Request.FileOperateType]
        DELETE_MAP_FILE: _ClassVar[Request.FileOperateType]
        RENAME_MAP_FILE: _ClassVar[Request.FileOperateType]
        EXPORT_LOG_FILE: _ClassVar[Request.FileOperateType]
        EXPORT_CONFIG_FILE: _ClassVar[Request.FileOperateType]
        IMPORT_CONFIG_FILE: _ClassVar[Request.FileOperateType]
        IMPORT_SYSTEM_UPDATE_FILE: _ClassVar[Request.FileOperateType]
        RESTORE_FACTORY_SETTINGS: _ClassVar[Request.FileOperateType]
        BACKUP_AS_FACTORY_SETTINGS: _ClassVar[Request.FileOperateType]
        GET_COMMON_FILES: _ClassVar[Request.FileOperateType]
        SET_COMMON_FILES: _ClassVar[Request.FileOperateType]
        EXPORT_NAV_MAP_FILE: _ClassVar[Request.FileOperateType]
        EXPORT_OPT_MAP_FILE: _ClassVar[Request.FileOperateType]
        EXPORT_ALL_MAP_FILE: _ClassVar[Request.FileOperateType]
    FILE_OPERATE_ZERO: Request.FileOperateType
    GET_NAV_MAP_FILE: Request.FileOperateType
    SET_NAV_MAP_FILE: Request.FileOperateType
    GET_RAW_MAP_FILE: Request.FileOperateType
    SET_RAW_MAP_FILE: Request.FileOperateType
    EXPORT_MAP_FILE: Request.FileOperateType
    IMPORT_MAP_FILE: Request.FileOperateType
    DELETE_MAP_FILE: Request.FileOperateType
    RENAME_MAP_FILE: Request.FileOperateType
    EXPORT_LOG_FILE: Request.FileOperateType
    EXPORT_CONFIG_FILE: Request.FileOperateType
    IMPORT_CONFIG_FILE: Request.FileOperateType
    IMPORT_SYSTEM_UPDATE_FILE: Request.FileOperateType
    RESTORE_FACTORY_SETTINGS: Request.FileOperateType
    BACKUP_AS_FACTORY_SETTINGS: Request.FileOperateType
    GET_COMMON_FILES: Request.FileOperateType
    SET_COMMON_FILES: Request.FileOperateType
    EXPORT_NAV_MAP_FILE: Request.FileOperateType
    EXPORT_OPT_MAP_FILE: Request.FileOperateType
    EXPORT_ALL_MAP_FILE: Request.FileOperateType
    REQUEST_TYPE_FIELD_NUMBER: _ClassVar[int]
    LOGIN_REQUEST_FIELD_NUMBER: _ClassVar[int]
    FILE_OP_FIELD_NUMBER: _ClassVar[int]
    PARAM_STR_FIELD_NUMBER: _ClassVar[int]
    PARAM_STR1_FIELD_NUMBER: _ClassVar[int]
    PARAM_STR2_FIELD_NUMBER: _ClassVar[int]
    PARAM_INT_FIELD_NUMBER: _ClassVar[int]
    PARAM_INT1_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    TMP_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    REDRAW_POLYGON_FIELD_NUMBER: _ClassVar[int]
    LOCK_UNLOCK_AREA_FIELD_NUMBER: _ClassVar[int]
    BACK_POSE_IN_NET_FIELD_NUMBER: _ClassVar[int]
    request_type: Request.RequestType
    login_request: LoginRequest
    file_op: Request.FileOperateType
    param_str: str
    param_str1: str
    param_str2: str
    param_int: int
    param_int1: int
    config: _containers.RepeatedCompositeFieldContainer[ConfigItem]
    tmp_configs: _containers.RepeatedCompositeFieldContainer[TmpConfigItem]
    redraw_polygon: _containers.RepeatedCompositeFieldContainer[Polygon]
    lock_unlock_area: _containers.RepeatedCompositeFieldContainer[Point]
    back_pose_in_net: Pose
    def __init__(self, request_type: _Optional[_Union[Request.RequestType, str]] = ..., login_request: _Optional[_Union[LoginRequest, _Mapping]] = ..., file_op: _Optional[_Union[Request.FileOperateType, str]] = ..., param_str: _Optional[str] = ..., param_str1: _Optional[str] = ..., param_str2: _Optional[str] = ..., param_int: _Optional[int] = ..., param_int1: _Optional[int] = ..., config: _Optional[_Iterable[_Union[ConfigItem, _Mapping]]] = ..., tmp_configs: _Optional[_Iterable[_Union[TmpConfigItem, _Mapping]]] = ..., redraw_polygon: _Optional[_Iterable[_Union[Polygon, _Mapping]]] = ..., lock_unlock_area: _Optional[_Iterable[_Union[Point, _Mapping]]] = ..., back_pose_in_net: _Optional[_Union[Pose, _Mapping]] = ...) -> None: ...

class Notification(_message.Message):
    __slots__ = ["notify_type", "reserved_field", "cur_station_no", "cur_pose", "movement_task", "action_task", "cal_result", "update_result", "mission_list"]
    class NotifyType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NOTIFY_MOVE_TASK_FINISHED: _ClassVar[Notification.NotifyType]
        NOTIFY_ACTION_TASK_FINISHED: _ClassVar[Notification.NotifyType]
        NOTIFY_MOVE_PATH_SENT: _ClassVar[Notification.NotifyType]
        NOTIFY_CALIBRATION_FINISHED: _ClassVar[Notification.NotifyType]
        NOTIFY_UPDATE_FINISHED: _ClassVar[Notification.NotifyType]
        NOTIFY_MISSION_LIST_CHANGED: _ClassVar[Notification.NotifyType]
    NOTIFY_MOVE_TASK_FINISHED: Notification.NotifyType
    NOTIFY_ACTION_TASK_FINISHED: Notification.NotifyType
    NOTIFY_MOVE_PATH_SENT: Notification.NotifyType
    NOTIFY_CALIBRATION_FINISHED: Notification.NotifyType
    NOTIFY_UPDATE_FINISHED: Notification.NotifyType
    NOTIFY_MISSION_LIST_CHANGED: Notification.NotifyType
    NOTIFY_TYPE_FIELD_NUMBER: _ClassVar[int]
    RESERVED_FIELD_FIELD_NUMBER: _ClassVar[int]
    CUR_STATION_NO_FIELD_NUMBER: _ClassVar[int]
    CUR_POSE_FIELD_NUMBER: _ClassVar[int]
    MOVEMENT_TASK_FIELD_NUMBER: _ClassVar[int]
    ACTION_TASK_FIELD_NUMBER: _ClassVar[int]
    CAL_RESULT_FIELD_NUMBER: _ClassVar[int]
    UPDATE_RESULT_FIELD_NUMBER: _ClassVar[int]
    MISSION_LIST_FIELD_NUMBER: _ClassVar[int]
    notify_type: Notification.NotifyType
    reserved_field: int
    cur_station_no: int
    cur_pose: Pose
    movement_task: MovementTask
    action_task: ActionTask
    cal_result: CalibrationResult
    update_result: UpdateResult
    mission_list: _containers.RepeatedCompositeFieldContainer[Mission]
    def __init__(self, notify_type: _Optional[_Union[Notification.NotifyType, str]] = ..., reserved_field: _Optional[int] = ..., cur_station_no: _Optional[int] = ..., cur_pose: _Optional[_Union[Pose, _Mapping]] = ..., movement_task: _Optional[_Union[MovementTask, _Mapping]] = ..., action_task: _Optional[_Union[ActionTask, _Mapping]] = ..., cal_result: _Optional[_Union[CalibrationResult, _Mapping]] = ..., update_result: _Optional[_Union[UpdateResult, _Mapping]] = ..., mission_list: _Optional[_Iterable[_Union[Mission, _Mapping]]] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ["response_type", "info", "system_state", "hardware_state", "map_list", "laser_points", "movement_task", "action_task", "result", "notify_response", "config", "tmp_configs", "list", "record", "timestamp", "return_str", "mission_list", "common_poses_info", "address_info", "login_info", "connect_info", "registers", "feature_infos", "registers_values", "calibration_camera_result", "redraw_info", "debug_info", "back_pose_in_net", "sensor_samples", "camera_meta_info"]
    class ResponseType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        RESPONSE_LOGIN: _ClassVar[Response.ResponseType]
        RESPONSE_INFO: _ClassVar[Response.ResponseType]
        RESPONSE_ALL_STATE: _ClassVar[Response.ResponseType]
        RESPONSE_SYSTEM_STATE: _ClassVar[Response.ResponseType]
        RESPONSE_HARDWARE_STATE: _ClassVar[Response.ResponseType]
        RESPONSE_MAP_LIST: _ClassVar[Response.ResponseType]
        RESPONSE_BAG_LIST: _ClassVar[Response.ResponseType]
        RESPONSE_LASER_POINTS: _ClassVar[Response.ResponseType]
        RESPONSE_TASK_STATE: _ClassVar[Response.ResponseType]
        RESPONSE_COMMAND: _ClassVar[Response.ResponseType]
        RESPONSE_ADDRINFO: _ClassVar[Response.ResponseType]
        RESPONSE_NOTIFY: _ClassVar[Response.ResponseType]
        RESPONSE_FILE_OPERATE: _ClassVar[Response.ResponseType]
        RESPONSE_LOGOUT: _ClassVar[Response.ResponseType]
        RESPONSE_LOAD_CONFIG: _ClassVar[Response.ResponseType]
        RESPONSE_SAVE_CONFIG: _ClassVar[Response.ResponseType]
        RESPONSE_LOAD_TMP_CONFIG: _ClassVar[Response.ResponseType]
        RESPONSE_SAVE_TMP_CONFIG: _ClassVar[Response.ResponseType]
        RESPONSE_FILE_LIST: _ClassVar[Response.ResponseType]
        RESPONSE_MONITOR_DATA: _ClassVar[Response.ResponseType]
        RESPONSE_CHANGE_PW: _ClassVar[Response.ResponseType]
        RESPONSE_TIMESTAMP: _ClassVar[Response.ResponseType]
        RESPONSE_GET_CUR_MAP: _ClassVar[Response.ResponseType]
        RESPONSE_MISSION_LIST: _ClassVar[Response.ResponseType]
        RESPONSE_HEARTBEAT: _ClassVar[Response.ResponseType]
        RESPONSE_COMMON_POSE_INFO: _ClassVar[Response.ResponseType]
        RESPONSE_CONNECT_INFO: _ClassVar[Response.ResponseType]
        RESPONSE_FEATURE_INFO: _ClassVar[Response.ResponseType]
        RESPONSE_CAMERA_CALIBR_INFO: _ClassVar[Response.ResponseType]
        RESPONSE_REDRAW: _ClassVar[Response.ResponseType]
        RESPONSE_SYSTEM_CMD: _ClassVar[Response.ResponseType]
        RESPONSE_LOCK_SPACE: _ClassVar[Response.ResponseType]
        RESPONSE_UNLOCK_SPACE: _ClassVar[Response.ResponseType]
        RESPONSE_BACK_TO_PATH: _ClassVar[Response.ResponseType]
        RESPONSE_SENSOR_SAMPLES: _ClassVar[Response.ResponseType]
        RESPONSE_READ_DISCRETE_INPUTS: _ClassVar[Response.ResponseType]
        RESPONSE_READ_COILS: _ClassVar[Response.ResponseType]
        RESPONSE_WRITE_SINGLE_COIL: _ClassVar[Response.ResponseType]
        RESPONSE_WRITE_MULTIPLE_COILS: _ClassVar[Response.ResponseType]
        RESPONSE_READ_INPUT_REGISTER: _ClassVar[Response.ResponseType]
        RESPONSE_READ_HOLDING_REGISTERS: _ClassVar[Response.ResponseType]
        RESPONSE_WRITE_SINGLE_REGISTER: _ClassVar[Response.ResponseType]
        RESPONSE_WRITE_MULTIPLE_REGISTERS: _ClassVar[Response.ResponseType]
        RESPONSE_READ_ALL_REGISTERS: _ClassVar[Response.ResponseType]
        RESPONSE_GET_CAMERA_PICTURE: _ClassVar[Response.ResponseType]
    RESPONSE_LOGIN: Response.ResponseType
    RESPONSE_INFO: Response.ResponseType
    RESPONSE_ALL_STATE: Response.ResponseType
    RESPONSE_SYSTEM_STATE: Response.ResponseType
    RESPONSE_HARDWARE_STATE: Response.ResponseType
    RESPONSE_MAP_LIST: Response.ResponseType
    RESPONSE_BAG_LIST: Response.ResponseType
    RESPONSE_LASER_POINTS: Response.ResponseType
    RESPONSE_TASK_STATE: Response.ResponseType
    RESPONSE_COMMAND: Response.ResponseType
    RESPONSE_ADDRINFO: Response.ResponseType
    RESPONSE_NOTIFY: Response.ResponseType
    RESPONSE_FILE_OPERATE: Response.ResponseType
    RESPONSE_LOGOUT: Response.ResponseType
    RESPONSE_LOAD_CONFIG: Response.ResponseType
    RESPONSE_SAVE_CONFIG: Response.ResponseType
    RESPONSE_LOAD_TMP_CONFIG: Response.ResponseType
    RESPONSE_SAVE_TMP_CONFIG: Response.ResponseType
    RESPONSE_FILE_LIST: Response.ResponseType
    RESPONSE_MONITOR_DATA: Response.ResponseType
    RESPONSE_CHANGE_PW: Response.ResponseType
    RESPONSE_TIMESTAMP: Response.ResponseType
    RESPONSE_GET_CUR_MAP: Response.ResponseType
    RESPONSE_MISSION_LIST: Response.ResponseType
    RESPONSE_HEARTBEAT: Response.ResponseType
    RESPONSE_COMMON_POSE_INFO: Response.ResponseType
    RESPONSE_CONNECT_INFO: Response.ResponseType
    RESPONSE_FEATURE_INFO: Response.ResponseType
    RESPONSE_CAMERA_CALIBR_INFO: Response.ResponseType
    RESPONSE_REDRAW: Response.ResponseType
    RESPONSE_SYSTEM_CMD: Response.ResponseType
    RESPONSE_LOCK_SPACE: Response.ResponseType
    RESPONSE_UNLOCK_SPACE: Response.ResponseType
    RESPONSE_BACK_TO_PATH: Response.ResponseType
    RESPONSE_SENSOR_SAMPLES: Response.ResponseType
    RESPONSE_READ_DISCRETE_INPUTS: Response.ResponseType
    RESPONSE_READ_COILS: Response.ResponseType
    RESPONSE_WRITE_SINGLE_COIL: Response.ResponseType
    RESPONSE_WRITE_MULTIPLE_COILS: Response.ResponseType
    RESPONSE_READ_INPUT_REGISTER: Response.ResponseType
    RESPONSE_READ_HOLDING_REGISTERS: Response.ResponseType
    RESPONSE_WRITE_SINGLE_REGISTER: Response.ResponseType
    RESPONSE_WRITE_MULTIPLE_REGISTERS: Response.ResponseType
    RESPONSE_READ_ALL_REGISTERS: Response.ResponseType
    RESPONSE_GET_CAMERA_PICTURE: Response.ResponseType
    RESPONSE_TYPE_FIELD_NUMBER: _ClassVar[int]
    INFO_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_STATE_FIELD_NUMBER: _ClassVar[int]
    HARDWARE_STATE_FIELD_NUMBER: _ClassVar[int]
    MAP_LIST_FIELD_NUMBER: _ClassVar[int]
    LASER_POINTS_FIELD_NUMBER: _ClassVar[int]
    MOVEMENT_TASK_FIELD_NUMBER: _ClassVar[int]
    ACTION_TASK_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    NOTIFY_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    TMP_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    LIST_FIELD_NUMBER: _ClassVar[int]
    RECORD_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    RETURN_STR_FIELD_NUMBER: _ClassVar[int]
    MISSION_LIST_FIELD_NUMBER: _ClassVar[int]
    COMMON_POSES_INFO_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_INFO_FIELD_NUMBER: _ClassVar[int]
    LOGIN_INFO_FIELD_NUMBER: _ClassVar[int]
    CONNECT_INFO_FIELD_NUMBER: _ClassVar[int]
    REGISTERS_FIELD_NUMBER: _ClassVar[int]
    FEATURE_INFOS_FIELD_NUMBER: _ClassVar[int]
    REGISTERS_VALUES_FIELD_NUMBER: _ClassVar[int]
    CALIBRATION_CAMERA_RESULT_FIELD_NUMBER: _ClassVar[int]
    REDRAW_INFO_FIELD_NUMBER: _ClassVar[int]
    DEBUG_INFO_FIELD_NUMBER: _ClassVar[int]
    BACK_POSE_IN_NET_FIELD_NUMBER: _ClassVar[int]
    SENSOR_SAMPLES_FIELD_NUMBER: _ClassVar[int]
    CAMERA_META_INFO_FIELD_NUMBER: _ClassVar[int]
    response_type: Response.ResponseType
    info: Info
    system_state: SystemState
    hardware_state: HardwareState
    map_list: MapList
    laser_points: LaserPoints
    movement_task: MovementTask
    action_task: ActionTask
    result: ResponseResult
    notify_response: NotifyResponse
    config: _containers.RepeatedCompositeFieldContainer[ConfigItem]
    tmp_configs: _containers.RepeatedCompositeFieldContainer[TmpConfigItem]
    list: FileList
    record: _monitor_pb2.Record
    timestamp: int
    return_str: str
    mission_list: _containers.RepeatedCompositeFieldContainer[Mission]
    common_poses_info: CommonPosesInfo
    address_info: AddressInfo
    login_info: LoginInfo
    connect_info: ConnectInfo
    registers: bytes
    feature_infos: _containers.RepeatedCompositeFieldContainer[FeatureInfos]
    registers_values: RegistersValuesResult
    calibration_camera_result: CalibrationCameraResult
    redraw_info: RedrawInfo
    debug_info: DebugInfo
    back_pose_in_net: Pose
    sensor_samples: _monitor_pb2.SensorDataCollection
    camera_meta_info: CameraMetaInfo
    def __init__(self, response_type: _Optional[_Union[Response.ResponseType, str]] = ..., info: _Optional[_Union[Info, _Mapping]] = ..., system_state: _Optional[_Union[SystemState, _Mapping]] = ..., hardware_state: _Optional[_Union[HardwareState, _Mapping]] = ..., map_list: _Optional[_Union[MapList, _Mapping]] = ..., laser_points: _Optional[_Union[LaserPoints, _Mapping]] = ..., movement_task: _Optional[_Union[MovementTask, _Mapping]] = ..., action_task: _Optional[_Union[ActionTask, _Mapping]] = ..., result: _Optional[_Union[ResponseResult, _Mapping]] = ..., notify_response: _Optional[_Union[NotifyResponse, _Mapping]] = ..., config: _Optional[_Iterable[_Union[ConfigItem, _Mapping]]] = ..., tmp_configs: _Optional[_Iterable[_Union[TmpConfigItem, _Mapping]]] = ..., list: _Optional[_Union[FileList, _Mapping]] = ..., record: _Optional[_Union[_monitor_pb2.Record, _Mapping]] = ..., timestamp: _Optional[int] = ..., return_str: _Optional[str] = ..., mission_list: _Optional[_Iterable[_Union[Mission, _Mapping]]] = ..., common_poses_info: _Optional[_Union[CommonPosesInfo, _Mapping]] = ..., address_info: _Optional[_Union[AddressInfo, _Mapping]] = ..., login_info: _Optional[_Union[LoginInfo, _Mapping]] = ..., connect_info: _Optional[_Union[ConnectInfo, _Mapping]] = ..., registers: _Optional[bytes] = ..., feature_infos: _Optional[_Iterable[_Union[FeatureInfos, _Mapping]]] = ..., registers_values: _Optional[_Union[RegistersValuesResult, _Mapping]] = ..., calibration_camera_result: _Optional[_Union[CalibrationCameraResult, _Mapping]] = ..., redraw_info: _Optional[_Union[RedrawInfo, _Mapping]] = ..., debug_info: _Optional[_Union[DebugInfo, _Mapping]] = ..., back_pose_in_net: _Optional[_Union[Pose, _Mapping]] = ..., sensor_samples: _Optional[_Union[_monitor_pb2.SensorDataCollection, _Mapping]] = ..., camera_meta_info: _Optional[_Union[CameraMetaInfo, _Mapping]] = ...) -> None: ...

class CalibrationCameraResult(_message.Message):
    __slots__ = ["flag", "str_1", "str_2"]
    FLAG_FIELD_NUMBER: _ClassVar[int]
    STR_1_FIELD_NUMBER: _ClassVar[int]
    STR_2_FIELD_NUMBER: _ClassVar[int]
    flag: bool
    str_1: str
    str_2: str
    def __init__(self, flag: bool = ..., str_1: _Optional[str] = ..., str_2: _Optional[str] = ...) -> None: ...

class CalibrationResult(_message.Message):
    __slots__ = ["x", "y", "theta", "status"]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    THETA_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    theta: float
    status: int
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., theta: _Optional[float] = ..., status: _Optional[int] = ...) -> None: ...

class UpdateResult(_message.Message):
    __slots__ = ["result_code"]
    class ResultCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        UPDATE_SUCCESS: _ClassVar[UpdateResult.ResultCode]
        UPDATE_FAILED: _ClassVar[UpdateResult.ResultCode]
    UPDATE_SUCCESS: UpdateResult.ResultCode
    UPDATE_FAILED: UpdateResult.ResultCode
    RESULT_CODE_FIELD_NUMBER: _ClassVar[int]
    result_code: UpdateResult.ResultCode
    def __init__(self, result_code: _Optional[_Union[UpdateResult.ResultCode, str]] = ...) -> None: ...

class NotifyResponse(_message.Message):
    __slots__ = ["ack", "type"]
    class NotifyType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NOTIFY_MOVE_TASK_FINISHED: _ClassVar[NotifyResponse.NotifyType]
        NOTIFY_ACTION_TASK_FINISHED: _ClassVar[NotifyResponse.NotifyType]
        NOTIFY_MOVE_PATH_SENT: _ClassVar[NotifyResponse.NotifyType]
        NOTIFY_CALIBRATION_FINISHED: _ClassVar[NotifyResponse.NotifyType]
        NOTIFY_UPDATE_FINISHED: _ClassVar[NotifyResponse.NotifyType]
    NOTIFY_MOVE_TASK_FINISHED: NotifyResponse.NotifyType
    NOTIFY_ACTION_TASK_FINISHED: NotifyResponse.NotifyType
    NOTIFY_MOVE_PATH_SENT: NotifyResponse.NotifyType
    NOTIFY_CALIBRATION_FINISHED: NotifyResponse.NotifyType
    NOTIFY_UPDATE_FINISHED: NotifyResponse.NotifyType
    ACK_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ack: bool
    type: NotifyResponse.NotifyType
    def __init__(self, ack: bool = ..., type: _Optional[_Union[NotifyResponse.NotifyType, str]] = ...) -> None: ...

class TmpConfigItem(_message.Message):
    __slots__ = ["key", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class ConfigItem(_message.Message):
    __slots__ = ["id", "key", "value", "name", "value_unit", "value_type", "default_value", "value_range", "description", "permission", "changed_time", "changed_user"]
    ID_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_UNIT_FIELD_NUMBER: _ClassVar[int]
    VALUE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_VALUE_FIELD_NUMBER: _ClassVar[int]
    VALUE_RANGE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PERMISSION_FIELD_NUMBER: _ClassVar[int]
    CHANGED_TIME_FIELD_NUMBER: _ClassVar[int]
    CHANGED_USER_FIELD_NUMBER: _ClassVar[int]
    id: int
    key: str
    value: str
    name: str
    value_unit: str
    value_type: str
    default_value: str
    value_range: str
    description: str
    permission: int
    changed_time: str
    changed_user: str
    def __init__(self, id: _Optional[int] = ..., key: _Optional[str] = ..., value: _Optional[str] = ..., name: _Optional[str] = ..., value_unit: _Optional[str] = ..., value_type: _Optional[str] = ..., default_value: _Optional[str] = ..., value_range: _Optional[str] = ..., description: _Optional[str] = ..., permission: _Optional[int] = ..., changed_time: _Optional[str] = ..., changed_user: _Optional[str] = ...) -> None: ...

class LoginInfo(_message.Message):
    __slots__ = ["session_id", "result_str"]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    RESULT_STR_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    result_str: str
    def __init__(self, session_id: _Optional[int] = ..., result_str: _Optional[str] = ...) -> None: ...

class LoginRequest(_message.Message):
    __slots__ = ["username", "password", "access"]
    class AccessAuthority(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        AA_NONE: _ClassVar[LoginRequest.AccessAuthority]
        AA_NORMAL: _ClassVar[LoginRequest.AccessAuthority]
        AA_ADMIN: _ClassVar[LoginRequest.AccessAuthority]
        AA_ROOT: _ClassVar[LoginRequest.AccessAuthority]
    AA_NONE: LoginRequest.AccessAuthority
    AA_NORMAL: LoginRequest.AccessAuthority
    AA_ADMIN: LoginRequest.AccessAuthority
    AA_ROOT: LoginRequest.AccessAuthority
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    ACCESS_FIELD_NUMBER: _ClassVar[int]
    username: str
    password: str
    access: LoginRequest.AccessAuthority
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ..., access: _Optional[_Union[LoginRequest.AccessAuthority, str]] = ...) -> None: ...

class ResponseResult(_message.Message):
    __slots__ = ["result_state", "result_code"]
    class ResultState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        RESPONSE_NONE: _ClassVar[ResponseResult.ResultState]
        RESPONSE_PROCESSING: _ClassVar[ResponseResult.ResultState]
        RESPONSE_OK: _ClassVar[ResponseResult.ResultState]
        RESPONSE_FAILED: _ClassVar[ResponseResult.ResultState]
    RESPONSE_NONE: ResponseResult.ResultState
    RESPONSE_PROCESSING: ResponseResult.ResultState
    RESPONSE_OK: ResponseResult.ResultState
    RESPONSE_FAILED: ResponseResult.ResultState
    class ResultCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        RESULT_CODE_NONE: _ClassVar[ResponseResult.ResultCode]
        RESULT_PRE_TASK_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_INVALID_CMD_PARAM: _ClassVar[ResponseResult.ResultCode]
        RESULT_PRE_TASK_WAITING_ACK: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_IN_EMERGENCY_STATE: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_NO_LOCATING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_USER_OR_PASSWORD_INVALID: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_UNDEFINED: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_CONTROL_MUTEX_IS_LOCKED: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCATION_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCATION_SLAM_STATE_ERROR: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCATION_STATION_NOT_EXIST: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCATION_NO_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCATION_PATH_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCATION_MOVEMENT_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCATION_MISSON_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_CANCEL_EMERGENCY_CAN_NOT_RECOVER: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_CONTINUE_IN_EMERGENCY: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_SYNC_TIME_SYSTEM_NOT_IDLE: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MANUAL_CONTROL_NOT_ON: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_START_MANUAL_CONTROL_IN_EMERGENCY: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_START_MANUAL_CONTROL_IN_BREAK_SW: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MANUAL_CONTROL_MOVEMENT_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MANUAL_CONTROL_MISSION_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_NEW_MAP_MOVEMENT_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_NEW_MAP_MISSION_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_SET_MAP_PATH_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_SET_MAP_MOVEMENT_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_SET_MAP_MISSION_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_SET_CONFIG_MOVEMENT_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_SET_CONFIG_ACTION_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_SET_CONFIG_MISSION_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_SET_SPEED_NOT_IN_MANUAL: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_SET_PGV_INFO_ID_IS_ZERO: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_SET_PGV_INFO_ID_IS_REPEAT: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCK_CONTROL_MUTEX_MOVEMENT_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCK_CONTROL_MUTEX_ACTION_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCK_CONTROL_MUTEX_MISSION_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCK_CONTROL_MUTEX_NONE_NICK_NAME: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_LOCK_CONTROL_MUTEX_NONE_IP_ADDRESS: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_UNLOCK_CONTROL_MUTEX_CURRENT_IS_UNLOCKED: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_UNLOCK_CONTROL_MUTEX_SESSION_ID_MISSMATCH: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_FORCE_UNLOCK_CONTROL_MUTEX_PERMISSION_DENIED: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_IN_EMERGENCY: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_NO_LOCATING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_PRE_TASK_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_INVALID_CMD_PARAM: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_IN_MANUAL_CONTROL: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_IN_MISSION_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_FOLLOW_PATH_START_POSE_OFFSET: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_FOLLOW_PATH_EXIST_ARC: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_FOLLOW_PATH_START_ANGLE_OFFSET: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_FOLLOW_PATH_POSE_NOT_CONTINUOUS: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_FOLLOW_PATH_ANGLE_NOT_CONTINUOUS: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_IN_POWER_SAVE_MODE: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_BREAK_SWITCH_ON: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_LASER_ERROR: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_VSC_ERROR: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_SRC_ERROR: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_MOTOR1_ERROR: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MOVEMENT_MOTOR2_ERROR: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_ACTION_IN_EMERGENCY: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_ACTION_PRE_TASK_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_ACTION_IN_POWER_SAVE_MODE: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_ACTION_IN_MISSION_RUNNING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_ACTION_RESPONSE_TIMEOUT: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_ACTION_RESPONSE_INCORRECT: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_ACTION_SYSTEM_BUSY: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_ACTION_ID_NOT_SUPPORT: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_ACTION_PARAM_0_NOT_SUPPORT: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_ACTION_PARAM_1_NOT_SUPPORT: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_ACTION_EAC_DISABLED: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MISSION_IN_EMERGENCY: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MISSION_NO_LOCATING: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MISSION_ID_NOT_EXIST: _ClassVar[ResponseResult.ResultCode]
        RESULT_CODE_MISSION_ENQUEUE_TIMEOUT: _ClassVar[ResponseResult.ResultCode]
    RESULT_CODE_NONE: ResponseResult.ResultCode
    RESULT_PRE_TASK_RUNNING: ResponseResult.ResultCode
    RESULT_INVALID_CMD_PARAM: ResponseResult.ResultCode
    RESULT_PRE_TASK_WAITING_ACK: ResponseResult.ResultCode
    RESULT_CODE_IN_EMERGENCY_STATE: ResponseResult.ResultCode
    RESULT_CODE_NO_LOCATING: ResponseResult.ResultCode
    RESULT_CODE_USER_OR_PASSWORD_INVALID: ResponseResult.ResultCode
    RESULT_CODE_UNDEFINED: ResponseResult.ResultCode
    RESULT_CODE_CONTROL_MUTEX_IS_LOCKED: ResponseResult.ResultCode
    RESULT_CODE_LOCATION_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_LOCATION_SLAM_STATE_ERROR: ResponseResult.ResultCode
    RESULT_CODE_LOCATION_STATION_NOT_EXIST: ResponseResult.ResultCode
    RESULT_CODE_LOCATION_NO_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_LOCATION_PATH_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_LOCATION_MOVEMENT_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_LOCATION_MISSON_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_CANCEL_EMERGENCY_CAN_NOT_RECOVER: ResponseResult.ResultCode
    RESULT_CODE_CONTINUE_IN_EMERGENCY: ResponseResult.ResultCode
    RESULT_CODE_SYNC_TIME_SYSTEM_NOT_IDLE: ResponseResult.ResultCode
    RESULT_CODE_MANUAL_CONTROL_NOT_ON: ResponseResult.ResultCode
    RESULT_CODE_START_MANUAL_CONTROL_IN_EMERGENCY: ResponseResult.ResultCode
    RESULT_CODE_START_MANUAL_CONTROL_IN_BREAK_SW: ResponseResult.ResultCode
    RESULT_CODE_MANUAL_CONTROL_MOVEMENT_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_MANUAL_CONTROL_MISSION_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_NEW_MAP_MOVEMENT_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_NEW_MAP_MISSION_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_SET_MAP_PATH_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_SET_MAP_MOVEMENT_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_SET_MAP_MISSION_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_SET_CONFIG_MOVEMENT_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_SET_CONFIG_ACTION_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_SET_CONFIG_MISSION_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_SET_SPEED_NOT_IN_MANUAL: ResponseResult.ResultCode
    RESULT_CODE_SET_PGV_INFO_ID_IS_ZERO: ResponseResult.ResultCode
    RESULT_CODE_SET_PGV_INFO_ID_IS_REPEAT: ResponseResult.ResultCode
    RESULT_CODE_LOCK_CONTROL_MUTEX_MOVEMENT_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_LOCK_CONTROL_MUTEX_ACTION_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_LOCK_CONTROL_MUTEX_MISSION_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_LOCK_CONTROL_MUTEX_NONE_NICK_NAME: ResponseResult.ResultCode
    RESULT_CODE_LOCK_CONTROL_MUTEX_NONE_IP_ADDRESS: ResponseResult.ResultCode
    RESULT_CODE_UNLOCK_CONTROL_MUTEX_CURRENT_IS_UNLOCKED: ResponseResult.ResultCode
    RESULT_CODE_UNLOCK_CONTROL_MUTEX_SESSION_ID_MISSMATCH: ResponseResult.ResultCode
    RESULT_CODE_FORCE_UNLOCK_CONTROL_MUTEX_PERMISSION_DENIED: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_IN_EMERGENCY: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_NO_LOCATING: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_PRE_TASK_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_INVALID_CMD_PARAM: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_IN_MANUAL_CONTROL: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_IN_MISSION_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_FOLLOW_PATH_START_POSE_OFFSET: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_FOLLOW_PATH_EXIST_ARC: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_FOLLOW_PATH_START_ANGLE_OFFSET: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_FOLLOW_PATH_POSE_NOT_CONTINUOUS: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_FOLLOW_PATH_ANGLE_NOT_CONTINUOUS: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_IN_POWER_SAVE_MODE: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_BREAK_SWITCH_ON: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_LASER_ERROR: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_VSC_ERROR: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_SRC_ERROR: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_MOTOR1_ERROR: ResponseResult.ResultCode
    RESULT_CODE_MOVEMENT_MOTOR2_ERROR: ResponseResult.ResultCode
    RESULT_CODE_ACTION_IN_EMERGENCY: ResponseResult.ResultCode
    RESULT_CODE_ACTION_PRE_TASK_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_ACTION_IN_POWER_SAVE_MODE: ResponseResult.ResultCode
    RESULT_CODE_ACTION_IN_MISSION_RUNNING: ResponseResult.ResultCode
    RESULT_CODE_ACTION_RESPONSE_TIMEOUT: ResponseResult.ResultCode
    RESULT_CODE_ACTION_RESPONSE_INCORRECT: ResponseResult.ResultCode
    RESULT_CODE_ACTION_SYSTEM_BUSY: ResponseResult.ResultCode
    RESULT_CODE_ACTION_ID_NOT_SUPPORT: ResponseResult.ResultCode
    RESULT_CODE_ACTION_PARAM_0_NOT_SUPPORT: ResponseResult.ResultCode
    RESULT_CODE_ACTION_PARAM_1_NOT_SUPPORT: ResponseResult.ResultCode
    RESULT_CODE_ACTION_EAC_DISABLED: ResponseResult.ResultCode
    RESULT_CODE_MISSION_IN_EMERGENCY: ResponseResult.ResultCode
    RESULT_CODE_MISSION_NO_LOCATING: ResponseResult.ResultCode
    RESULT_CODE_MISSION_ID_NOT_EXIST: ResponseResult.ResultCode
    RESULT_CODE_MISSION_ENQUEUE_TIMEOUT: ResponseResult.ResultCode
    RESULT_STATE_FIELD_NUMBER: _ClassVar[int]
    RESULT_CODE_FIELD_NUMBER: _ClassVar[int]
    result_state: ResponseResult.ResultState
    result_code: int
    def __init__(self, result_state: _Optional[_Union[ResponseResult.ResultState, str]] = ..., result_code: _Optional[int] = ...) -> None: ...

class Command(_message.Message):
    __slots__ = ["command", "param_int", "param_int1", "param_int2", "param_int3", "param_str", "pose", "param_boolean", "param_str1", "movement_task", "action_task", "general_io_output", "mission_list", "locker_ip_address", "locker_nickname", "paths"]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    PARAM_INT_FIELD_NUMBER: _ClassVar[int]
    PARAM_INT1_FIELD_NUMBER: _ClassVar[int]
    PARAM_INT2_FIELD_NUMBER: _ClassVar[int]
    PARAM_INT3_FIELD_NUMBER: _ClassVar[int]
    PARAM_STR_FIELD_NUMBER: _ClassVar[int]
    POSE_FIELD_NUMBER: _ClassVar[int]
    PARAM_BOOLEAN_FIELD_NUMBER: _ClassVar[int]
    PARAM_STR1_FIELD_NUMBER: _ClassVar[int]
    MOVEMENT_TASK_FIELD_NUMBER: _ClassVar[int]
    ACTION_TASK_FIELD_NUMBER: _ClassVar[int]
    GENERAL_IO_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    MISSION_LIST_FIELD_NUMBER: _ClassVar[int]
    LOCKER_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    LOCKER_NICKNAME_FIELD_NUMBER: _ClassVar[int]
    PATHS_FIELD_NUMBER: _ClassVar[int]
    command: CommandType
    param_int: int
    param_int1: int
    param_int2: int
    param_int3: int
    param_str: str
    pose: Pose
    param_boolean: bool
    param_str1: str
    movement_task: MovementTask
    action_task: ActionTask
    general_io_output: int
    mission_list: _containers.RepeatedCompositeFieldContainer[Mission]
    locker_ip_address: str
    locker_nickname: str
    paths: _containers.RepeatedCompositeFieldContainer[Path]
    def __init__(self, command: _Optional[_Union[CommandType, str]] = ..., param_int: _Optional[int] = ..., param_int1: _Optional[int] = ..., param_int2: _Optional[int] = ..., param_int3: _Optional[int] = ..., param_str: _Optional[str] = ..., pose: _Optional[_Union[Pose, _Mapping]] = ..., param_boolean: bool = ..., param_str1: _Optional[str] = ..., movement_task: _Optional[_Union[MovementTask, _Mapping]] = ..., action_task: _Optional[_Union[ActionTask, _Mapping]] = ..., general_io_output: _Optional[int] = ..., mission_list: _Optional[_Iterable[_Union[Mission, _Mapping]]] = ..., locker_ip_address: _Optional[str] = ..., locker_nickname: _Optional[str] = ..., paths: _Optional[_Iterable[_Union[Path, _Mapping]]] = ...) -> None: ...

class Pose(_message.Message):
    __slots__ = ["x", "y", "z", "roll", "pitch", "yaw", "confidence"]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    ROLL_FIELD_NUMBER: _ClassVar[int]
    PITCH_FIELD_NUMBER: _ClassVar[int]
    YAW_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    z: int
    roll: int
    pitch: int
    yaw: int
    confidence: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ..., z: _Optional[int] = ..., roll: _Optional[int] = ..., pitch: _Optional[int] = ..., yaw: _Optional[int] = ..., confidence: _Optional[int] = ...) -> None: ...

class FileInfo(_message.Message):
    __slots__ = ["name", "size", "last_write_time", "file_compressed", "md5sum"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    LAST_WRITE_TIME_FIELD_NUMBER: _ClassVar[int]
    FILE_COMPRESSED_FIELD_NUMBER: _ClassVar[int]
    MD5SUM_FIELD_NUMBER: _ClassVar[int]
    name: str
    size: int
    last_write_time: int
    file_compressed: bool
    md5sum: str
    def __init__(self, name: _Optional[str] = ..., size: _Optional[int] = ..., last_write_time: _Optional[int] = ..., file_compressed: bool = ..., md5sum: _Optional[str] = ...) -> None: ...

class MapList(_message.Message):
    __slots__ = ["req_seq", "list"]
    REQ_SEQ_FIELD_NUMBER: _ClassVar[int]
    LIST_FIELD_NUMBER: _ClassVar[int]
    req_seq: int
    list: _containers.RepeatedCompositeFieldContainer[FileInfo]
    def __init__(self, req_seq: _Optional[int] = ..., list: _Optional[_Iterable[_Union[FileInfo, _Mapping]]] = ...) -> None: ...

class FileList(_message.Message):
    __slots__ = ["req_seq", "list"]
    REQ_SEQ_FIELD_NUMBER: _ClassVar[int]
    LIST_FIELD_NUMBER: _ClassVar[int]
    req_seq: int
    list: _containers.RepeatedCompositeFieldContainer[FileInfo]
    def __init__(self, req_seq: _Optional[int] = ..., list: _Optional[_Iterable[_Union[FileInfo, _Mapping]]] = ...) -> None: ...

class TriggerCondition(_message.Message):
    __slots__ = ["load_state"]
    class LoadState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        LOAD_STATE_NONE: _ClassVar[TriggerCondition.LoadState]
        LOAD_STATE_FREE: _ClassVar[TriggerCondition.LoadState]
        LOAD_STATE_FULL: _ClassVar[TriggerCondition.LoadState]
    LOAD_STATE_NONE: TriggerCondition.LoadState
    LOAD_STATE_FREE: TriggerCondition.LoadState
    LOAD_STATE_FULL: TriggerCondition.LoadState
    LOAD_STATE_FIELD_NUMBER: _ClassVar[int]
    load_state: TriggerCondition.LoadState
    def __init__(self, load_state: _Optional[_Union[TriggerCondition.LoadState, str]] = ...) -> None: ...

class PathBehavior(_message.Message):
    __slots__ = ["type", "trigger_stage", "trigger_condition"]
    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        TYPE_DEFAULT: _ClassVar[PathBehavior.Type]
        TYPE_MOVE_DOCKING_BASED_ON_UPCAMERA_QRCODE: _ClassVar[PathBehavior.Type]
    TYPE_DEFAULT: PathBehavior.Type
    TYPE_MOVE_DOCKING_BASED_ON_UPCAMERA_QRCODE: PathBehavior.Type
    class TriggerStage(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        TRIGGER_TYPE_NONE: _ClassVar[PathBehavior.TriggerStage]
        TRIGGER_TYPE_BEFORE_ENTERING: _ClassVar[PathBehavior.TriggerStage]
    TRIGGER_TYPE_NONE: PathBehavior.TriggerStage
    TRIGGER_TYPE_BEFORE_ENTERING: PathBehavior.TriggerStage
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_STAGE_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_CONDITION_FIELD_NUMBER: _ClassVar[int]
    type: PathBehavior.Type
    trigger_stage: PathBehavior.TriggerStage
    trigger_condition: TriggerCondition
    def __init__(self, type: _Optional[_Union[PathBehavior.Type, str]] = ..., trigger_stage: _Optional[_Union[PathBehavior.TriggerStage, str]] = ..., trigger_condition: _Optional[_Union[TriggerCondition, _Mapping]] = ...) -> None: ...

class Path(_message.Message):
    __slots__ = ["type", "sx", "sy", "ex", "ey", "cx", "cy", "dx", "dy", "radius", "rotate_angle", "direction", "limit_v", "limit_w", "limit_rotate_angle", "orientation", "path_behavior"]
    class PathType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        PATH_ZERO: _ClassVar[Path.PathType]
        PATH_LINE: _ClassVar[Path.PathType]
        PATH_CIRCLE: _ClassVar[Path.PathType]
        PATH_BEZIER: _ClassVar[Path.PathType]
        PATH_ROTATE: _ClassVar[Path.PathType]
    PATH_ZERO: Path.PathType
    PATH_LINE: Path.PathType
    PATH_CIRCLE: Path.PathType
    PATH_BEZIER: Path.PathType
    PATH_ROTATE: Path.PathType
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SX_FIELD_NUMBER: _ClassVar[int]
    SY_FIELD_NUMBER: _ClassVar[int]
    EX_FIELD_NUMBER: _ClassVar[int]
    EY_FIELD_NUMBER: _ClassVar[int]
    CX_FIELD_NUMBER: _ClassVar[int]
    CY_FIELD_NUMBER: _ClassVar[int]
    DX_FIELD_NUMBER: _ClassVar[int]
    DY_FIELD_NUMBER: _ClassVar[int]
    RADIUS_FIELD_NUMBER: _ClassVar[int]
    ROTATE_ANGLE_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    LIMIT_V_FIELD_NUMBER: _ClassVar[int]
    LIMIT_W_FIELD_NUMBER: _ClassVar[int]
    LIMIT_ROTATE_ANGLE_FIELD_NUMBER: _ClassVar[int]
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    PATH_BEHAVIOR_FIELD_NUMBER: _ClassVar[int]
    type: Path.PathType
    sx: int
    sy: int
    ex: int
    ey: int
    cx: int
    cy: int
    dx: int
    dy: int
    radius: int
    rotate_angle: int
    direction: int
    limit_v: int
    limit_w: int
    limit_rotate_angle: int
    orientation: int
    path_behavior: PathBehavior
    def __init__(self, type: _Optional[_Union[Path.PathType, str]] = ..., sx: _Optional[int] = ..., sy: _Optional[int] = ..., ex: _Optional[int] = ..., ey: _Optional[int] = ..., cx: _Optional[int] = ..., cy: _Optional[int] = ..., dx: _Optional[int] = ..., dy: _Optional[int] = ..., radius: _Optional[int] = ..., rotate_angle: _Optional[int] = ..., direction: _Optional[int] = ..., limit_v: _Optional[int] = ..., limit_w: _Optional[int] = ..., limit_rotate_angle: _Optional[int] = ..., orientation: _Optional[int] = ..., path_behavior: _Optional[_Union[PathBehavior, _Mapping]] = ...) -> None: ...

class PathList(_message.Message):
    __slots__ = ["list"]
    LIST_FIELD_NUMBER: _ClassVar[int]
    list: _containers.RepeatedCompositeFieldContainer[Path]
    def __init__(self, list: _Optional[_Iterable[_Union[Path, _Mapping]]] = ...) -> None: ...

class Info(_message.Message):
    __slots__ = ["serial_no", "nickname", "hardware_version", "kernel_release", "sros_version", "sros_version_str", "src_version", "src_version_str", "vehicle_type", "action_unit", "vehicle_serial_no"]
    SERIAL_NO_FIELD_NUMBER: _ClassVar[int]
    NICKNAME_FIELD_NUMBER: _ClassVar[int]
    HARDWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    KERNEL_RELEASE_FIELD_NUMBER: _ClassVar[int]
    SROS_VERSION_FIELD_NUMBER: _ClassVar[int]
    SROS_VERSION_STR_FIELD_NUMBER: _ClassVar[int]
    SRC_VERSION_FIELD_NUMBER: _ClassVar[int]
    SRC_VERSION_STR_FIELD_NUMBER: _ClassVar[int]
    VEHICLE_TYPE_FIELD_NUMBER: _ClassVar[int]
    ACTION_UNIT_FIELD_NUMBER: _ClassVar[int]
    VEHICLE_SERIAL_NO_FIELD_NUMBER: _ClassVar[int]
    serial_no: str
    nickname: str
    hardware_version: str
    kernel_release: str
    sros_version: int
    sros_version_str: str
    src_version: int
    src_version_str: str
    vehicle_type: str
    action_unit: str
    vehicle_serial_no: str
    def __init__(self, serial_no: _Optional[str] = ..., nickname: _Optional[str] = ..., hardware_version: _Optional[str] = ..., kernel_release: _Optional[str] = ..., sros_version: _Optional[int] = ..., sros_version_str: _Optional[str] = ..., src_version: _Optional[int] = ..., src_version_str: _Optional[str] = ..., vehicle_type: _Optional[str] = ..., action_unit: _Optional[str] = ..., vehicle_serial_no: _Optional[str] = ...) -> None: ...

class MotionControlState(_message.Message):
    __slots__ = ["state", "v_x", "v_y", "w", "path_no"]
    class MCState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        MC_ZERO: _ClassVar[MotionControlState.MCState]
        MC_INITIALING: _ClassVar[MotionControlState.MCState]
        MC_IDLE: _ClassVar[MotionControlState.MCState]
        MC_PATH_RUNNING: _ClassVar[MotionControlState.MCState]
        MC_VELOCITY_RUNNING: _ClassVar[MotionControlState.MCState]
    MC_ZERO: MotionControlState.MCState
    MC_INITIALING: MotionControlState.MCState
    MC_IDLE: MotionControlState.MCState
    MC_PATH_RUNNING: MotionControlState.MCState
    MC_VELOCITY_RUNNING: MotionControlState.MCState
    STATE_FIELD_NUMBER: _ClassVar[int]
    V_X_FIELD_NUMBER: _ClassVar[int]
    V_Y_FIELD_NUMBER: _ClassVar[int]
    W_FIELD_NUMBER: _ClassVar[int]
    PATH_NO_FIELD_NUMBER: _ClassVar[int]
    state: MotionControlState.MCState
    v_x: int
    v_y: int
    w: int
    path_no: int
    def __init__(self, state: _Optional[_Union[MotionControlState.MCState, str]] = ..., v_x: _Optional[int] = ..., v_y: _Optional[int] = ..., w: _Optional[int] = ..., path_no: _Optional[int] = ...) -> None: ...

class MovementTask(_message.Message):
    __slots__ = ["state", "no", "session_id", "dst_station_type", "type", "stations", "poses", "paths", "paths_replacement_times", "avoid_policy", "cur_path_no", "cur_checkpoint_no", "remain_time", "remain_distance", "total_distance", "result", "failed_code", "station_pgv_info", "force_nav_on_map", "length", "width", "load_type"]
    class TaskState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        MT_NA: _ClassVar[MovementTask.TaskState]
        MT_WAIT_FOR_START: _ClassVar[MovementTask.TaskState]
        MT_RUNNING: _ClassVar[MovementTask.TaskState]
        MT_PAUSED: _ClassVar[MovementTask.TaskState]
        MT_FINISHED: _ClassVar[MovementTask.TaskState]
        MT_IN_CANCEL: _ClassVar[MovementTask.TaskState]
        MT_TASK_WAIT_FOR_ACK: _ClassVar[MovementTask.TaskState]
        MT_WAIT_FOR_CHECKPOINT: _ClassVar[MovementTask.TaskState]
    MT_NA: MovementTask.TaskState
    MT_WAIT_FOR_START: MovementTask.TaskState
    MT_RUNNING: MovementTask.TaskState
    MT_PAUSED: MovementTask.TaskState
    MT_FINISHED: MovementTask.TaskState
    MT_IN_CANCEL: MovementTask.TaskState
    MT_TASK_WAIT_FOR_ACK: MovementTask.TaskState
    MT_WAIT_FOR_CHECKPOINT: MovementTask.TaskState
    class DstStationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        DS_DEFAULT: _ClassVar[MovementTask.DstStationType]
        DS_NO_ROTATE: _ClassVar[MovementTask.DstStationType]
    DS_DEFAULT: MovementTask.DstStationType
    DS_NO_ROTATE: MovementTask.DstStationType
    class TaskType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        MT_ZERO: _ClassVar[MovementTask.TaskType]
        MT_MOVE_FOLLOW_PATH: _ClassVar[MovementTask.TaskType]
        MT_MOVE_TO_STATION: _ClassVar[MovementTask.TaskType]
        MT_MOVE_TO_POSE: _ClassVar[MovementTask.TaskType]
        MT_MOVE_MIX2: _ClassVar[MovementTask.TaskType]
    MT_ZERO: MovementTask.TaskType
    MT_MOVE_FOLLOW_PATH: MovementTask.TaskType
    MT_MOVE_TO_STATION: MovementTask.TaskType
    MT_MOVE_TO_POSE: MovementTask.TaskType
    MT_MOVE_MIX2: MovementTask.TaskType
    class AvoidPolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        AT_ZERO: _ClassVar[MovementTask.AvoidPolicy]
        OBSTACLE_AVOID_WAIT: _ClassVar[MovementTask.AvoidPolicy]
        OBSTACLE_AVOID_REPLAN: _ClassVar[MovementTask.AvoidPolicy]
        OBSTACLE_AVOID_NONE: _ClassVar[MovementTask.AvoidPolicy]
    AT_ZERO: MovementTask.AvoidPolicy
    OBSTACLE_AVOID_WAIT: MovementTask.AvoidPolicy
    OBSTACLE_AVOID_REPLAN: MovementTask.AvoidPolicy
    OBSTACLE_AVOID_NONE: MovementTask.AvoidPolicy
    class FailedCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        UNKNOWN_FAILED: _ClassVar[MovementTask.FailedCode]
        FAILED_CODE_NAV_FIND_PATH_NO_STATION_IN_MAP: _ClassVar[MovementTask.FailedCode]
        FAILED_CODE_NAV_FIND_PATH_NET_NAV_AND_FREE_NAV_BOTH_DISABLED: _ClassVar[MovementTask.FailedCode]
        FAILED_CODE_NET_NAV_START_POSE_NOT_ON_NET: _ClassVar[MovementTask.FailedCode]
        FAILED_CODE_NET_NAV_DST_POSE_NOT_ON_NET: _ClassVar[MovementTask.FailedCode]
        FAILED_CODE_NET_NAV_NONE_STATION_AROUND_AGV: _ClassVar[MovementTask.FailedCode]
        FAILED_CODE_NET_NAV_FINDE_PATH_NO_WAY: _ClassVar[MovementTask.FailedCode]
        FAILED_CODE_FREE_NAV_DST_POSE_UNWALKABLE: _ClassVar[MovementTask.FailedCode]
        FAILED_CODE_FREE_NAV_NO_WAY: _ClassVar[MovementTask.FailedCode]
        FAILED_CODE_AGV_NOT_ARRIVED_DEST: _ClassVar[MovementTask.FailedCode]
    UNKNOWN_FAILED: MovementTask.FailedCode
    FAILED_CODE_NAV_FIND_PATH_NO_STATION_IN_MAP: MovementTask.FailedCode
    FAILED_CODE_NAV_FIND_PATH_NET_NAV_AND_FREE_NAV_BOTH_DISABLED: MovementTask.FailedCode
    FAILED_CODE_NET_NAV_START_POSE_NOT_ON_NET: MovementTask.FailedCode
    FAILED_CODE_NET_NAV_DST_POSE_NOT_ON_NET: MovementTask.FailedCode
    FAILED_CODE_NET_NAV_NONE_STATION_AROUND_AGV: MovementTask.FailedCode
    FAILED_CODE_NET_NAV_FINDE_PATH_NO_WAY: MovementTask.FailedCode
    FAILED_CODE_FREE_NAV_DST_POSE_UNWALKABLE: MovementTask.FailedCode
    FAILED_CODE_FREE_NAV_NO_WAY: MovementTask.FailedCode
    FAILED_CODE_AGV_NOT_ARRIVED_DEST: MovementTask.FailedCode
    STATE_FIELD_NUMBER: _ClassVar[int]
    NO_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    DST_STATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    STATIONS_FIELD_NUMBER: _ClassVar[int]
    POSES_FIELD_NUMBER: _ClassVar[int]
    PATHS_FIELD_NUMBER: _ClassVar[int]
    PATHS_REPLACEMENT_TIMES_FIELD_NUMBER: _ClassVar[int]
    AVOID_POLICY_FIELD_NUMBER: _ClassVar[int]
    CUR_PATH_NO_FIELD_NUMBER: _ClassVar[int]
    CUR_CHECKPOINT_NO_FIELD_NUMBER: _ClassVar[int]
    REMAIN_TIME_FIELD_NUMBER: _ClassVar[int]
    REMAIN_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    FAILED_CODE_FIELD_NUMBER: _ClassVar[int]
    STATION_PGV_INFO_FIELD_NUMBER: _ClassVar[int]
    FORCE_NAV_ON_MAP_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    LOAD_TYPE_FIELD_NUMBER: _ClassVar[int]
    state: MovementTask.TaskState
    no: int
    session_id: int
    dst_station_type: MovementTask.DstStationType
    type: MovementTask.TaskType
    stations: _containers.RepeatedScalarFieldContainer[int]
    poses: _containers.RepeatedCompositeFieldContainer[Pose]
    paths: _containers.RepeatedCompositeFieldContainer[Path]
    paths_replacement_times: int
    avoid_policy: MovementTask.AvoidPolicy
    cur_path_no: int
    cur_checkpoint_no: int
    remain_time: int
    remain_distance: int
    total_distance: int
    result: TaskResult
    failed_code: int
    station_pgv_info: PgvInfo
    force_nav_on_map: bool
    length: int
    width: int
    load_type: str
    def __init__(self, state: _Optional[_Union[MovementTask.TaskState, str]] = ..., no: _Optional[int] = ..., session_id: _Optional[int] = ..., dst_station_type: _Optional[_Union[MovementTask.DstStationType, str]] = ..., type: _Optional[_Union[MovementTask.TaskType, str]] = ..., stations: _Optional[_Iterable[int]] = ..., poses: _Optional[_Iterable[_Union[Pose, _Mapping]]] = ..., paths: _Optional[_Iterable[_Union[Path, _Mapping]]] = ..., paths_replacement_times: _Optional[int] = ..., avoid_policy: _Optional[_Union[MovementTask.AvoidPolicy, str]] = ..., cur_path_no: _Optional[int] = ..., cur_checkpoint_no: _Optional[int] = ..., remain_time: _Optional[int] = ..., remain_distance: _Optional[int] = ..., total_distance: _Optional[int] = ..., result: _Optional[_Union[TaskResult, str]] = ..., failed_code: _Optional[int] = ..., station_pgv_info: _Optional[_Union[PgvInfo, _Mapping]] = ..., force_nav_on_map: bool = ..., length: _Optional[int] = ..., width: _Optional[int] = ..., load_type: _Optional[str] = ...) -> None: ...

class ActionTask(_message.Message):
    __slots__ = ["state", "no", "session_id", "id", "param0", "param1", "param2", "param_str", "result", "result_str", "result_code"]
    class TaskState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        AT_ZERO: _ClassVar[ActionTask.TaskState]
        AT_WAIT_FOR_START: _ClassVar[ActionTask.TaskState]
        AT_RUNNING: _ClassVar[ActionTask.TaskState]
        AT_PAUSED: _ClassVar[ActionTask.TaskState]
        AT_FINISHED: _ClassVar[ActionTask.TaskState]
        AT_IN_CANCEL: _ClassVar[ActionTask.TaskState]
        AT_TASK_WAIT_FOR_ACK: _ClassVar[ActionTask.TaskState]
    AT_ZERO: ActionTask.TaskState
    AT_WAIT_FOR_START: ActionTask.TaskState
    AT_RUNNING: ActionTask.TaskState
    AT_PAUSED: ActionTask.TaskState
    AT_FINISHED: ActionTask.TaskState
    AT_IN_CANCEL: ActionTask.TaskState
    AT_TASK_WAIT_FOR_ACK: ActionTask.TaskState
    STATE_FIELD_NUMBER: _ClassVar[int]
    NO_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    PARAM0_FIELD_NUMBER: _ClassVar[int]
    PARAM1_FIELD_NUMBER: _ClassVar[int]
    PARAM2_FIELD_NUMBER: _ClassVar[int]
    PARAM_STR_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    RESULT_STR_FIELD_NUMBER: _ClassVar[int]
    RESULT_CODE_FIELD_NUMBER: _ClassVar[int]
    state: ActionTask.TaskState
    no: int
    session_id: int
    id: int
    param0: int
    param1: int
    param2: int
    param_str: str
    result: TaskResult
    result_str: str
    result_code: int
    def __init__(self, state: _Optional[_Union[ActionTask.TaskState, str]] = ..., no: _Optional[int] = ..., session_id: _Optional[int] = ..., id: _Optional[int] = ..., param0: _Optional[int] = ..., param1: _Optional[int] = ..., param2: _Optional[int] = ..., param_str: _Optional[str] = ..., result: _Optional[_Union[TaskResult, str]] = ..., result_str: _Optional[str] = ..., result_code: _Optional[int] = ...) -> None: ...

class Mission(_message.Message):
    __slots__ = ["no", "id", "name", "map_name", "cur_step_id", "step_list", "avoid_policy", "state", "result", "error_code", "start_timestamp", "finish_timestamp", "total_cycle_time", "finish_cycle_time"]
    class MissionStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        MISSION_STATUS_NA: _ClassVar[Mission.MissionStatus]
        MISSION_STATUS_PENDING: _ClassVar[Mission.MissionStatus]
        MISSION_STATUS_RUNNING: _ClassVar[Mission.MissionStatus]
        MISSION_STATUS_PAUSED: _ClassVar[Mission.MissionStatus]
        MISSION_STATUS_FINISHED: _ClassVar[Mission.MissionStatus]
    MISSION_STATUS_NA: Mission.MissionStatus
    MISSION_STATUS_PENDING: Mission.MissionStatus
    MISSION_STATUS_RUNNING: Mission.MissionStatus
    MISSION_STATUS_PAUSED: Mission.MissionStatus
    MISSION_STATUS_FINISHED: Mission.MissionStatus
    NO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MAP_NAME_FIELD_NUMBER: _ClassVar[int]
    CUR_STEP_ID_FIELD_NUMBER: _ClassVar[int]
    STEP_LIST_FIELD_NUMBER: _ClassVar[int]
    AVOID_POLICY_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    START_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    FINISH_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CYCLE_TIME_FIELD_NUMBER: _ClassVar[int]
    FINISH_CYCLE_TIME_FIELD_NUMBER: _ClassVar[int]
    no: int
    id: int
    name: str
    map_name: str
    cur_step_id: str
    step_list: _containers.RepeatedCompositeFieldContainer[MissionStep]
    avoid_policy: AvoidPolicy
    state: Mission.MissionStatus
    result: TaskResult
    error_code: int
    start_timestamp: int
    finish_timestamp: int
    total_cycle_time: int
    finish_cycle_time: int
    def __init__(self, no: _Optional[int] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., map_name: _Optional[str] = ..., cur_step_id: _Optional[str] = ..., step_list: _Optional[_Iterable[_Union[MissionStep, _Mapping]]] = ..., avoid_policy: _Optional[_Union[AvoidPolicy, str]] = ..., state: _Optional[_Union[Mission.MissionStatus, str]] = ..., result: _Optional[_Union[TaskResult, str]] = ..., error_code: _Optional[int] = ..., start_timestamp: _Optional[int] = ..., finish_timestamp: _Optional[int] = ..., total_cycle_time: _Optional[int] = ..., finish_cycle_time: _Optional[int] = ...) -> None: ...

class MissionStep(_message.Message):
    __slots__ = ["id", "mission_id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    MISSION_ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    mission_id: int
    def __init__(self, id: _Optional[str] = ..., mission_id: _Optional[int] = ...) -> None: ...

class PgvInfo(_message.Message):
    __slots__ = ["pgv_no", "pgv_id", "x", "y", "yaw"]
    PGV_NO_FIELD_NUMBER: _ClassVar[int]
    PGV_ID_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    YAW_FIELD_NUMBER: _ClassVar[int]
    pgv_no: str
    pgv_id: int
    x: int
    y: int
    yaw: int
    def __init__(self, pgv_no: _Optional[str] = ..., pgv_id: _Optional[int] = ..., x: _Optional[int] = ..., y: _Optional[int] = ..., yaw: _Optional[int] = ...) -> None: ...

class ControlMutexInfo(_message.Message):
    __slots__ = ["session_id", "ip_address", "nick_name", "user_name"]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    NICK_NAME_FIELD_NUMBER: _ClassVar[int]
    USER_NAME_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    ip_address: str
    nick_name: str
    user_name: str
    def __init__(self, session_id: _Optional[int] = ..., ip_address: _Optional[str] = ..., nick_name: _Optional[str] = ..., user_name: _Optional[str] = ...) -> None: ...

class Fault(_message.Message):
    __slots__ = ["id", "response_behavior", "can_automatically_recover", "raise_timestamp", "level"]
    ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_BEHAVIOR_FIELD_NUMBER: _ClassVar[int]
    CAN_AUTOMATICALLY_RECOVER_FIELD_NUMBER: _ClassVar[int]
    RAISE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    id: int
    response_behavior: int
    can_automatically_recover: bool
    raise_timestamp: int
    level: int
    def __init__(self, id: _Optional[int] = ..., response_behavior: _Optional[int] = ..., can_automatically_recover: bool = ..., raise_timestamp: _Optional[int] = ..., level: _Optional[int] = ...) -> None: ...

class ForkliftState(_message.Message):
    __slots__ = ["arm_height", "steering_angle", "goods_pose", "fork_left_right_encoder_value", "fork_front_back_encoder_value"]
    ARM_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    STEERING_ANGLE_FIELD_NUMBER: _ClassVar[int]
    GOODS_POSE_FIELD_NUMBER: _ClassVar[int]
    FORK_LEFT_RIGHT_ENCODER_VALUE_FIELD_NUMBER: _ClassVar[int]
    FORK_FRONT_BACK_ENCODER_VALUE_FIELD_NUMBER: _ClassVar[int]
    arm_height: float
    steering_angle: float
    goods_pose: Pose
    fork_left_right_encoder_value: float
    fork_front_back_encoder_value: float
    def __init__(self, arm_height: _Optional[float] = ..., steering_angle: _Optional[float] = ..., goods_pose: _Optional[_Union[Pose, _Mapping]] = ..., fork_left_right_encoder_value: _Optional[float] = ..., fork_front_back_encoder_value: _Optional[float] = ...) -> None: ...

class RackInfoState(_message.Message):
    __slots__ = ["rack_name", "load_type", "rack_length", "rack_width", "rack_source", "rack_height", "rack_pose", "weight"]
    class RackInfoSource(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NONE: _ClassVar[RackInfoState.RackInfoSource]
        SROS: _ClassVar[RackInfoState.RackInfoSource]
        RIOT: _ClassVar[RackInfoState.RackInfoSource]
    NONE: RackInfoState.RackInfoSource
    SROS: RackInfoState.RackInfoSource
    RIOT: RackInfoState.RackInfoSource
    RACK_NAME_FIELD_NUMBER: _ClassVar[int]
    LOAD_TYPE_FIELD_NUMBER: _ClassVar[int]
    RACK_LENGTH_FIELD_NUMBER: _ClassVar[int]
    RACK_WIDTH_FIELD_NUMBER: _ClassVar[int]
    RACK_SOURCE_FIELD_NUMBER: _ClassVar[int]
    RACK_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    RACK_POSE_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    rack_name: str
    load_type: str
    rack_length: float
    rack_width: float
    rack_source: RackInfoState.RackInfoSource
    rack_height: float
    rack_pose: Pose
    weight: float
    def __init__(self, rack_name: _Optional[str] = ..., load_type: _Optional[str] = ..., rack_length: _Optional[float] = ..., rack_width: _Optional[float] = ..., rack_source: _Optional[_Union[RackInfoState.RackInfoSource, str]] = ..., rack_height: _Optional[float] = ..., rack_pose: _Optional[_Union[Pose, _Mapping]] = ..., weight: _Optional[float] = ...) -> None: ...

class SystemState(_message.Message):
    __slots__ = ["req_seq", "sys_state", "location_state", "location_pose", "emergency_state", "mc_state", "movement_state", "action_state", "station_no", "map_name", "map_saving_progress", "oba_enable_state", "fresh_state", "run_state", "load_state", "operation_state", "speed_level", "running_mission", "cur_pgv_info", "station_pgv_info", "global_pose_by_qr_code", "cur_volume", "control_mutex_lock_state", "control_mutex_info", "multi_load_state", "emergency_source", "new_movement_task_state", "last_error_code", "fault_codes", "faults", "fleet_mode", "rotate_value", "sync_rotate", "forklift_state", "manual_button_state", "manual_control_oba_state", "is_factory_mode", "is_poweroff_mode", "obstacle_model_info", "scheduling_mode", "location_type", "location_unconfirmed_source", "rack_info_state"]
    class SysState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        SYS_STATE_ZERO: _ClassVar[SystemState.SysState]
        SYS_STATE_INITIALING: _ClassVar[SystemState.SysState]
        SYS_STATE_IDLE: _ClassVar[SystemState.SysState]
        SYS_STATE_ERROR: _ClassVar[SystemState.SysState]
        SYS_STATE_START_LOCATING: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_NAV_INITIALING: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_NAV_FINDING_PATH: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_NAV_WAITING_FINISH: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_NAV_WAITING_FINISH_SLOW: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_NAV_REFINDING_PATH: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_NAV_PAUSED: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_NAV_NO_WAY: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_NEWMAP_DRAWING: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_NEWMAP_SAVING: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_PATH_NAV_INITIALING: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_PATH_WAITING_FINISH: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_PATH_WAITING_FINISH_SLOW: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_PATH_WAITING_CHECKPOINT: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_PATH_WAITING_CHECKPOINT_SLOW: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_PATH_PAUSED: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_NAV_NO_STATION: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_MANUAL_PAUSED: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_NAV_PATH_ERROR: _ClassVar[SystemState.SysState]
        SYS_STATE_TASK_MANUAL_PATH_ERROR: _ClassVar[SystemState.SysState]
        SYS_STATE_HARDWARE_ERROR: _ClassVar[SystemState.SysState]
    SYS_STATE_ZERO: SystemState.SysState
    SYS_STATE_INITIALING: SystemState.SysState
    SYS_STATE_IDLE: SystemState.SysState
    SYS_STATE_ERROR: SystemState.SysState
    SYS_STATE_START_LOCATING: SystemState.SysState
    SYS_STATE_TASK_NAV_INITIALING: SystemState.SysState
    SYS_STATE_TASK_NAV_FINDING_PATH: SystemState.SysState
    SYS_STATE_TASK_NAV_WAITING_FINISH: SystemState.SysState
    SYS_STATE_TASK_NAV_WAITING_FINISH_SLOW: SystemState.SysState
    SYS_STATE_TASK_NAV_REFINDING_PATH: SystemState.SysState
    SYS_STATE_TASK_NAV_PAUSED: SystemState.SysState
    SYS_STATE_TASK_NAV_NO_WAY: SystemState.SysState
    SYS_STATE_TASK_NEWMAP_DRAWING: SystemState.SysState
    SYS_STATE_TASK_NEWMAP_SAVING: SystemState.SysState
    SYS_STATE_TASK_PATH_NAV_INITIALING: SystemState.SysState
    SYS_STATE_TASK_PATH_WAITING_FINISH: SystemState.SysState
    SYS_STATE_TASK_PATH_WAITING_FINISH_SLOW: SystemState.SysState
    SYS_STATE_TASK_PATH_WAITING_CHECKPOINT: SystemState.SysState
    SYS_STATE_TASK_PATH_WAITING_CHECKPOINT_SLOW: SystemState.SysState
    SYS_STATE_TASK_PATH_PAUSED: SystemState.SysState
    SYS_STATE_TASK_NAV_NO_STATION: SystemState.SysState
    SYS_STATE_TASK_MANUAL_PAUSED: SystemState.SysState
    SYS_STATE_TASK_NAV_PATH_ERROR: SystemState.SysState
    SYS_STATE_TASK_MANUAL_PATH_ERROR: SystemState.SysState
    SYS_STATE_HARDWARE_ERROR: SystemState.SysState
    class LocationState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        LOCATION_STATE_ZERO: _ClassVar[SystemState.LocationState]
        LOCATION_STATE_NONE: _ClassVar[SystemState.LocationState]
        LOCATION_STATE_INITIALING: _ClassVar[SystemState.LocationState]
        LOCATION_STATE_RUNNING: _ClassVar[SystemState.LocationState]
        LOCATION_STATE_RELOCATING: _ClassVar[SystemState.LocationState]
        LOCATION_STATE_ERROR: _ClassVar[SystemState.LocationState]
    LOCATION_STATE_ZERO: SystemState.LocationState
    LOCATION_STATE_NONE: SystemState.LocationState
    LOCATION_STATE_INITIALING: SystemState.LocationState
    LOCATION_STATE_RUNNING: SystemState.LocationState
    LOCATION_STATE_RELOCATING: SystemState.LocationState
    LOCATION_STATE_ERROR: SystemState.LocationState
    class EmergencyState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        STATE_EMERGENCY_NA: _ClassVar[SystemState.EmergencyState]
        STATE_EMERGENCY_NONE: _ClassVar[SystemState.EmergencyState]
        STATE_EMERGENCY_TRIGGER: _ClassVar[SystemState.EmergencyState]
        STATE_EMERGENCY_RECOVERABLE: _ClassVar[SystemState.EmergencyState]
    STATE_EMERGENCY_NA: SystemState.EmergencyState
    STATE_EMERGENCY_NONE: SystemState.EmergencyState
    STATE_EMERGENCY_TRIGGER: SystemState.EmergencyState
    STATE_EMERGENCY_RECOVERABLE: SystemState.EmergencyState
    class ObaEnableState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        OBA_NA: _ClassVar[SystemState.ObaEnableState]
        OBA_ENABLED: _ClassVar[SystemState.ObaEnableState]
        OBA_DISABLED: _ClassVar[SystemState.ObaEnableState]
    OBA_NA: SystemState.ObaEnableState
    OBA_ENABLED: SystemState.ObaEnableState
    OBA_DISABLED: SystemState.ObaEnableState
    class FreshState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        FRESH_NA: _ClassVar[SystemState.FreshState]
        FRESH_NO: _ClassVar[SystemState.FreshState]
        FRESH_YES: _ClassVar[SystemState.FreshState]
    FRESH_NA: SystemState.FreshState
    FRESH_NO: SystemState.FreshState
    FRESH_YES: SystemState.FreshState
    class RunState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        RUN_NA: _ClassVar[SystemState.RunState]
        RUN_IDLE: _ClassVar[SystemState.RunState]
        RUN_RUNNING: _ClassVar[SystemState.RunState]
        RUN_BLOCK_SLOWDOWN: _ClassVar[SystemState.RunState]
        RUN_BLOCK_STOP: _ClassVar[SystemState.RunState]
    RUN_NA: SystemState.RunState
    RUN_IDLE: SystemState.RunState
    RUN_RUNNING: SystemState.RunState
    RUN_BLOCK_SLOWDOWN: SystemState.RunState
    RUN_BLOCK_STOP: SystemState.RunState
    class LoadState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        LOAD_NONE: _ClassVar[SystemState.LoadState]
        LOAD_FREE: _ClassVar[SystemState.LoadState]
        LOAD_FULL: _ClassVar[SystemState.LoadState]
    LOAD_NONE: SystemState.LoadState
    LOAD_FREE: SystemState.LoadState
    LOAD_FULL: SystemState.LoadState
    class OperationState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        OPERATION_NONE: _ClassVar[SystemState.OperationState]
        OPERATION_AUTO: _ClassVar[SystemState.OperationState]
        OPERATION_MANUAL: _ClassVar[SystemState.OperationState]
    OPERATION_NONE: SystemState.OperationState
    OPERATION_AUTO: SystemState.OperationState
    OPERATION_MANUAL: SystemState.OperationState
    class ControlMutexLockState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NONE: _ClassVar[SystemState.ControlMutexLockState]
        LOCKED: _ClassVar[SystemState.ControlMutexLockState]
        UNLOCKED: _ClassVar[SystemState.ControlMutexLockState]
    NONE: SystemState.ControlMutexLockState
    LOCKED: SystemState.ControlMutexLockState
    UNLOCKED: SystemState.ControlMutexLockState
    class EmergencySource(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        EMERGENCY_SRC_NONE: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_BUTTON_1: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_BUTTON_2: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_BUTTON_3: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_BUTTON_4: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_EDGE_1: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_EDGE_2: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_EDGE_3: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_EDGE_4: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_SOFTWARE_1: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_SOFTWARE_2: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_SOFTWARE_3: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SROS_HREART_BEAT_TIMEOUT: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_BATTERY_DOOR: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_SAFETY_LIDAR: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_INTERNAL_FAULT: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_EXTERNAL_FAULT: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_NXP_ESTOP: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_ST_ESTOP: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_TK1_ESTOP: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRC_ESTOP_OUT: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRTOS_MC_LOST_CTRL: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_SRTOS_TASK_BLOCKED: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_CE_FRONT_SECURITY_LIDAR: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_CE_BACK_SECURITY_LIDAR: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_CE_LEFT_ENCODER: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_CE_RIGHT_ENCODER: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_CE_LEFT_CONTACTOR: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_CE_RIGHT_CONTACTOR: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_RIOT_API_OPERATOR: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_RIOT_DEVICE_SAFE: _ClassVar[SystemState.EmergencySource]
        EMERGENCY_RIOT_MANUAL_CONTROL_SAFE: _ClassVar[SystemState.EmergencySource]
    EMERGENCY_SRC_NONE: SystemState.EmergencySource
    EMERGENCY_SRC_BUTTON_1: SystemState.EmergencySource
    EMERGENCY_SRC_BUTTON_2: SystemState.EmergencySource
    EMERGENCY_SRC_BUTTON_3: SystemState.EmergencySource
    EMERGENCY_SRC_BUTTON_4: SystemState.EmergencySource
    EMERGENCY_SRC_EDGE_1: SystemState.EmergencySource
    EMERGENCY_SRC_EDGE_2: SystemState.EmergencySource
    EMERGENCY_SRC_EDGE_3: SystemState.EmergencySource
    EMERGENCY_SRC_EDGE_4: SystemState.EmergencySource
    EMERGENCY_SRC_SOFTWARE_1: SystemState.EmergencySource
    EMERGENCY_SRC_SOFTWARE_2: SystemState.EmergencySource
    EMERGENCY_SRC_SOFTWARE_3: SystemState.EmergencySource
    EMERGENCY_SROS_HREART_BEAT_TIMEOUT: SystemState.EmergencySource
    EMERGENCY_SRC_BATTERY_DOOR: SystemState.EmergencySource
    EMERGENCY_SRC_SAFETY_LIDAR: SystemState.EmergencySource
    EMERGENCY_SRC_INTERNAL_FAULT: SystemState.EmergencySource
    EMERGENCY_SRC_EXTERNAL_FAULT: SystemState.EmergencySource
    EMERGENCY_SRC_NXP_ESTOP: SystemState.EmergencySource
    EMERGENCY_SRC_ST_ESTOP: SystemState.EmergencySource
    EMERGENCY_SRC_TK1_ESTOP: SystemState.EmergencySource
    EMERGENCY_SRC_ESTOP_OUT: SystemState.EmergencySource
    EMERGENCY_SRTOS_MC_LOST_CTRL: SystemState.EmergencySource
    EMERGENCY_SRTOS_TASK_BLOCKED: SystemState.EmergencySource
    EMERGENCY_CE_FRONT_SECURITY_LIDAR: SystemState.EmergencySource
    EMERGENCY_CE_BACK_SECURITY_LIDAR: SystemState.EmergencySource
    EMERGENCY_CE_LEFT_ENCODER: SystemState.EmergencySource
    EMERGENCY_CE_RIGHT_ENCODER: SystemState.EmergencySource
    EMERGENCY_CE_LEFT_CONTACTOR: SystemState.EmergencySource
    EMERGENCY_CE_RIGHT_CONTACTOR: SystemState.EmergencySource
    EMERGENCY_RIOT_API_OPERATOR: SystemState.EmergencySource
    EMERGENCY_RIOT_DEVICE_SAFE: SystemState.EmergencySource
    EMERGENCY_RIOT_MANUAL_CONTROL_SAFE: SystemState.EmergencySource
    class NewMovementTaskState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NEW_MOVEMENT_TASK_STATE_NONE: _ClassVar[SystemState.NewMovementTaskState]
        NEW_MOVEMENT_TASK_STATE_READY: _ClassVar[SystemState.NewMovementTaskState]
        NEW_MOVEMENT_TASK_STATE_USELESS: _ClassVar[SystemState.NewMovementTaskState]
    NEW_MOVEMENT_TASK_STATE_NONE: SystemState.NewMovementTaskState
    NEW_MOVEMENT_TASK_STATE_READY: SystemState.NewMovementTaskState
    NEW_MOVEMENT_TASK_STATE_USELESS: SystemState.NewMovementTaskState
    class FleetMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        FLEET_MODE_NONE: _ClassVar[SystemState.FleetMode]
        FLEET_MODE_OFFLINE: _ClassVar[SystemState.FleetMode]
        FLEET_MODE_ONLINE: _ClassVar[SystemState.FleetMode]
    FLEET_MODE_NONE: SystemState.FleetMode
    FLEET_MODE_OFFLINE: SystemState.FleetMode
    FLEET_MODE_ONLINE: SystemState.FleetMode
    class ManualButtonState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        ManualButton_NONE: _ClassVar[SystemState.ManualButtonState]
        ManualButton_AUTO: _ClassVar[SystemState.ManualButtonState]
        ManualButton_MANUAL: _ClassVar[SystemState.ManualButtonState]
    ManualButton_NONE: SystemState.ManualButtonState
    ManualButton_AUTO: SystemState.ManualButtonState
    ManualButton_MANUAL: SystemState.ManualButtonState
    class SchedulingMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        MODE_NONE: _ClassVar[SystemState.SchedulingMode]
        MODE_MANUAL: _ClassVar[SystemState.SchedulingMode]
        MODE_AUTOMATIC: _ClassVar[SystemState.SchedulingMode]
        MODE_MAINTENANCE: _ClassVar[SystemState.SchedulingMode]
    MODE_NONE: SystemState.SchedulingMode
    MODE_MANUAL: SystemState.SchedulingMode
    MODE_AUTOMATIC: SystemState.SchedulingMode
    MODE_MAINTENANCE: SystemState.SchedulingMode
    class LocationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        LOCATION_TYPE_NONE: _ClassVar[SystemState.LocationType]
        LOCATION_TYPE_LASER: _ClassVar[SystemState.LocationType]
        LOCATION_TYPE_QR_CODE: _ClassVar[SystemState.LocationType]
        LOCATION_TYPE_LMK: _ClassVar[SystemState.LocationType]
        LOCATION_TYPE_ACTION_ODOMETRY: _ClassVar[SystemState.LocationType]
        LOCATION_TYPE_ODOMETRY: _ClassVar[SystemState.LocationType]
        LOCATION_TYPE_DISABLE_MAP: _ClassVar[SystemState.LocationType]
    LOCATION_TYPE_NONE: SystemState.LocationType
    LOCATION_TYPE_LASER: SystemState.LocationType
    LOCATION_TYPE_QR_CODE: SystemState.LocationType
    LOCATION_TYPE_LMK: SystemState.LocationType
    LOCATION_TYPE_ACTION_ODOMETRY: SystemState.LocationType
    LOCATION_TYPE_ODOMETRY: SystemState.LocationType
    LOCATION_TYPE_DISABLE_MAP: SystemState.LocationType
    class LocationUnconfirmedSource(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        LOCATION_UNCONFIRMED_SOURCE_NONE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_BOOT_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_INIT_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_CORRIDOR_ENV_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_SIMILAR_ENV_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_LOW_SCORE_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_DYNAMIC_ENV_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_WIDE_ENV_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_HIGH_SCORE_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_LANDMARK_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_MIRROR_ENV_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_QR_CODE_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_SLIDE_ENV_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
        LOCATION_UNCONFIRMED_SOURCE_SLOPE_ENV_POSE: _ClassVar[SystemState.LocationUnconfirmedSource]
    LOCATION_UNCONFIRMED_SOURCE_NONE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_BOOT_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_INIT_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_CORRIDOR_ENV_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_SIMILAR_ENV_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_LOW_SCORE_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_DYNAMIC_ENV_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_WIDE_ENV_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_HIGH_SCORE_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_LANDMARK_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_MIRROR_ENV_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_QR_CODE_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_SLIDE_ENV_POSE: SystemState.LocationUnconfirmedSource
    LOCATION_UNCONFIRMED_SOURCE_SLOPE_ENV_POSE: SystemState.LocationUnconfirmedSource
    REQ_SEQ_FIELD_NUMBER: _ClassVar[int]
    SYS_STATE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_STATE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_POSE_FIELD_NUMBER: _ClassVar[int]
    EMERGENCY_STATE_FIELD_NUMBER: _ClassVar[int]
    MC_STATE_FIELD_NUMBER: _ClassVar[int]
    MOVEMENT_STATE_FIELD_NUMBER: _ClassVar[int]
    ACTION_STATE_FIELD_NUMBER: _ClassVar[int]
    STATION_NO_FIELD_NUMBER: _ClassVar[int]
    MAP_NAME_FIELD_NUMBER: _ClassVar[int]
    MAP_SAVING_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    OBA_ENABLE_STATE_FIELD_NUMBER: _ClassVar[int]
    FRESH_STATE_FIELD_NUMBER: _ClassVar[int]
    RUN_STATE_FIELD_NUMBER: _ClassVar[int]
    LOAD_STATE_FIELD_NUMBER: _ClassVar[int]
    OPERATION_STATE_FIELD_NUMBER: _ClassVar[int]
    SPEED_LEVEL_FIELD_NUMBER: _ClassVar[int]
    RUNNING_MISSION_FIELD_NUMBER: _ClassVar[int]
    CUR_PGV_INFO_FIELD_NUMBER: _ClassVar[int]
    STATION_PGV_INFO_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_POSE_BY_QR_CODE_FIELD_NUMBER: _ClassVar[int]
    CUR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    CONTROL_MUTEX_LOCK_STATE_FIELD_NUMBER: _ClassVar[int]
    CONTROL_MUTEX_INFO_FIELD_NUMBER: _ClassVar[int]
    MULTI_LOAD_STATE_FIELD_NUMBER: _ClassVar[int]
    EMERGENCY_SOURCE_FIELD_NUMBER: _ClassVar[int]
    NEW_MOVEMENT_TASK_STATE_FIELD_NUMBER: _ClassVar[int]
    LAST_ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    FAULT_CODES_FIELD_NUMBER: _ClassVar[int]
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    FLEET_MODE_FIELD_NUMBER: _ClassVar[int]
    ROTATE_VALUE_FIELD_NUMBER: _ClassVar[int]
    SYNC_ROTATE_FIELD_NUMBER: _ClassVar[int]
    FORKLIFT_STATE_FIELD_NUMBER: _ClassVar[int]
    MANUAL_BUTTON_STATE_FIELD_NUMBER: _ClassVar[int]
    MANUAL_CONTROL_OBA_STATE_FIELD_NUMBER: _ClassVar[int]
    IS_FACTORY_MODE_FIELD_NUMBER: _ClassVar[int]
    IS_POWEROFF_MODE_FIELD_NUMBER: _ClassVar[int]
    OBSTACLE_MODEL_INFO_FIELD_NUMBER: _ClassVar[int]
    SCHEDULING_MODE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_UNCONFIRMED_SOURCE_FIELD_NUMBER: _ClassVar[int]
    RACK_INFO_STATE_FIELD_NUMBER: _ClassVar[int]
    req_seq: int
    sys_state: SystemState.SysState
    location_state: SystemState.LocationState
    location_pose: Pose
    emergency_state: SystemState.EmergencyState
    mc_state: MotionControlState
    movement_state: MovementTask
    action_state: ActionTask
    station_no: int
    map_name: str
    map_saving_progress: int
    oba_enable_state: SystemState.ObaEnableState
    fresh_state: SystemState.FreshState
    run_state: SystemState.RunState
    load_state: SystemState.LoadState
    operation_state: SystemState.OperationState
    speed_level: int
    running_mission: Mission
    cur_pgv_info: PgvInfo
    station_pgv_info: PgvInfo
    global_pose_by_qr_code: PgvInfo
    cur_volume: int
    control_mutex_lock_state: SystemState.ControlMutexLockState
    control_mutex_info: ControlMutexInfo
    multi_load_state: int
    emergency_source: SystemState.EmergencySource
    new_movement_task_state: SystemState.NewMovementTaskState
    last_error_code: int
    fault_codes: _containers.RepeatedScalarFieldContainer[int]
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    fleet_mode: SystemState.FleetMode
    rotate_value: int
    sync_rotate: bool
    forklift_state: ForkliftState
    manual_button_state: SystemState.ManualButtonState
    manual_control_oba_state: bool
    is_factory_mode: bool
    is_poweroff_mode: bool
    obstacle_model_info: ObstacleModelInfo
    scheduling_mode: SystemState.SchedulingMode
    location_type: SystemState.LocationType
    location_unconfirmed_source: SystemState.LocationUnconfirmedSource
    rack_info_state: RackInfoState
    def __init__(self, req_seq: _Optional[int] = ..., sys_state: _Optional[_Union[SystemState.SysState, str]] = ..., location_state: _Optional[_Union[SystemState.LocationState, str]] = ..., location_pose: _Optional[_Union[Pose, _Mapping]] = ..., emergency_state: _Optional[_Union[SystemState.EmergencyState, str]] = ..., mc_state: _Optional[_Union[MotionControlState, _Mapping]] = ..., movement_state: _Optional[_Union[MovementTask, _Mapping]] = ..., action_state: _Optional[_Union[ActionTask, _Mapping]] = ..., station_no: _Optional[int] = ..., map_name: _Optional[str] = ..., map_saving_progress: _Optional[int] = ..., oba_enable_state: _Optional[_Union[SystemState.ObaEnableState, str]] = ..., fresh_state: _Optional[_Union[SystemState.FreshState, str]] = ..., run_state: _Optional[_Union[SystemState.RunState, str]] = ..., load_state: _Optional[_Union[SystemState.LoadState, str]] = ..., operation_state: _Optional[_Union[SystemState.OperationState, str]] = ..., speed_level: _Optional[int] = ..., running_mission: _Optional[_Union[Mission, _Mapping]] = ..., cur_pgv_info: _Optional[_Union[PgvInfo, _Mapping]] = ..., station_pgv_info: _Optional[_Union[PgvInfo, _Mapping]] = ..., global_pose_by_qr_code: _Optional[_Union[PgvInfo, _Mapping]] = ..., cur_volume: _Optional[int] = ..., control_mutex_lock_state: _Optional[_Union[SystemState.ControlMutexLockState, str]] = ..., control_mutex_info: _Optional[_Union[ControlMutexInfo, _Mapping]] = ..., multi_load_state: _Optional[int] = ..., emergency_source: _Optional[_Union[SystemState.EmergencySource, str]] = ..., new_movement_task_state: _Optional[_Union[SystemState.NewMovementTaskState, str]] = ..., last_error_code: _Optional[int] = ..., fault_codes: _Optional[_Iterable[int]] = ..., faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ..., fleet_mode: _Optional[_Union[SystemState.FleetMode, str]] = ..., rotate_value: _Optional[int] = ..., sync_rotate: bool = ..., forklift_state: _Optional[_Union[ForkliftState, _Mapping]] = ..., manual_button_state: _Optional[_Union[SystemState.ManualButtonState, str]] = ..., manual_control_oba_state: bool = ..., is_factory_mode: bool = ..., is_poweroff_mode: bool = ..., obstacle_model_info: _Optional[_Union[ObstacleModelInfo, _Mapping]] = ..., scheduling_mode: _Optional[_Union[SystemState.SchedulingMode, str]] = ..., location_type: _Optional[_Union[SystemState.LocationType, str]] = ..., location_unconfirmed_source: _Optional[_Union[SystemState.LocationUnconfirmedSource, str]] = ..., rack_info_state: _Optional[_Union[RackInfoState, _Mapping]] = ...) -> None: ...

class HardwareState(_message.Message):
    __slots__ = ["req_seq", "cpu_usage", "memory_usage", "disk_usage", "remain_disk_space", "wifi_state", "wifi_name", "wifi_strength", "battery_state", "battery_percentage", "battery_voltage", "battery_current", "battery_temperature", "battery_remain_capacity", "battery_nominal_capacity", "battery_use_cycles", "battery_remain_time", "battery_sn", "power_state", "break_sw_state", "laser_state", "cpu_temperature", "box_temperature", "box_temperature_max", "box_temperature_min", "box_humidity_max", "box_humidity_min", "fan_switch_state", "general_io_input", "general_io_output", "src_hardware_state", "devices", "hardware_state", "hardware_error_code", "ip_address"]
    class WiFiState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        WIFI_NA: _ClassVar[HardwareState.WiFiState]
        WIFI_DISCONNECTED: _ClassVar[HardwareState.WiFiState]
        WIFI_CONNECTED: _ClassVar[HardwareState.WiFiState]
        WIFI_SCANNING: _ClassVar[HardwareState.WiFiState]
    WIFI_NA: HardwareState.WiFiState
    WIFI_DISCONNECTED: HardwareState.WiFiState
    WIFI_CONNECTED: HardwareState.WiFiState
    WIFI_SCANNING: HardwareState.WiFiState
    class BatteryState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        BATTERY_NA: _ClassVar[HardwareState.BatteryState]
        BATTERY_CHARGING: _ClassVar[HardwareState.BatteryState]
        BATTERY_NO_CHARGING: _ClassVar[HardwareState.BatteryState]
    BATTERY_NA: HardwareState.BatteryState
    BATTERY_CHARGING: HardwareState.BatteryState
    BATTERY_NO_CHARGING: HardwareState.BatteryState
    class PowerState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        POWER_NA: _ClassVar[HardwareState.PowerState]
        POWER_NORMAL: _ClassVar[HardwareState.PowerState]
        POWER_SAVE_MODE: _ClassVar[HardwareState.PowerState]
    POWER_NA: HardwareState.PowerState
    POWER_NORMAL: HardwareState.PowerState
    POWER_SAVE_MODE: HardwareState.PowerState
    class BreakSwitchState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        BREAK_SW_NA: _ClassVar[HardwareState.BreakSwitchState]
        BREAK_SW_OFF: _ClassVar[HardwareState.BreakSwitchState]
        BREAK_SW_ON: _ClassVar[HardwareState.BreakSwitchState]
    BREAK_SW_NA: HardwareState.BreakSwitchState
    BREAK_SW_OFF: HardwareState.BreakSwitchState
    BREAK_SW_ON: HardwareState.BreakSwitchState
    class LaserState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        LASER_NA: _ClassVar[HardwareState.LaserState]
        LASER_INITING: _ClassVar[HardwareState.LaserState]
        LASER_OK: _ClassVar[HardwareState.LaserState]
        LASER_ERROR: _ClassVar[HardwareState.LaserState]
    LASER_NA: HardwareState.LaserState
    LASER_INITING: HardwareState.LaserState
    LASER_OK: HardwareState.LaserState
    LASER_ERROR: HardwareState.LaserState
    class HState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        H_STATE_ZERO: _ClassVar[HardwareState.HState]
        H_STATE_INITIALING: _ClassVar[HardwareState.HState]
        H_STATE_OK: _ClassVar[HardwareState.HState]
        H_STATE_ERROR: _ClassVar[HardwareState.HState]
    H_STATE_ZERO: HardwareState.HState
    H_STATE_INITIALING: HardwareState.HState
    H_STATE_OK: HardwareState.HState
    H_STATE_ERROR: HardwareState.HState
    REQ_SEQ_FIELD_NUMBER: _ClassVar[int]
    CPU_USAGE_FIELD_NUMBER: _ClassVar[int]
    MEMORY_USAGE_FIELD_NUMBER: _ClassVar[int]
    DISK_USAGE_FIELD_NUMBER: _ClassVar[int]
    REMAIN_DISK_SPACE_FIELD_NUMBER: _ClassVar[int]
    WIFI_STATE_FIELD_NUMBER: _ClassVar[int]
    WIFI_NAME_FIELD_NUMBER: _ClassVar[int]
    WIFI_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    BATTERY_STATE_FIELD_NUMBER: _ClassVar[int]
    BATTERY_PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    BATTERY_VOLTAGE_FIELD_NUMBER: _ClassVar[int]
    BATTERY_CURRENT_FIELD_NUMBER: _ClassVar[int]
    BATTERY_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    BATTERY_REMAIN_CAPACITY_FIELD_NUMBER: _ClassVar[int]
    BATTERY_NOMINAL_CAPACITY_FIELD_NUMBER: _ClassVar[int]
    BATTERY_USE_CYCLES_FIELD_NUMBER: _ClassVar[int]
    BATTERY_REMAIN_TIME_FIELD_NUMBER: _ClassVar[int]
    BATTERY_SN_FIELD_NUMBER: _ClassVar[int]
    POWER_STATE_FIELD_NUMBER: _ClassVar[int]
    BREAK_SW_STATE_FIELD_NUMBER: _ClassVar[int]
    LASER_STATE_FIELD_NUMBER: _ClassVar[int]
    CPU_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    BOX_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    BOX_TEMPERATURE_MAX_FIELD_NUMBER: _ClassVar[int]
    BOX_TEMPERATURE_MIN_FIELD_NUMBER: _ClassVar[int]
    BOX_HUMIDITY_MAX_FIELD_NUMBER: _ClassVar[int]
    BOX_HUMIDITY_MIN_FIELD_NUMBER: _ClassVar[int]
    FAN_SWITCH_STATE_FIELD_NUMBER: _ClassVar[int]
    GENERAL_IO_INPUT_FIELD_NUMBER: _ClassVar[int]
    GENERAL_IO_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    SRC_HARDWARE_STATE_FIELD_NUMBER: _ClassVar[int]
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    HARDWARE_STATE_FIELD_NUMBER: _ClassVar[int]
    HARDWARE_ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    req_seq: int
    cpu_usage: int
    memory_usage: int
    disk_usage: int
    remain_disk_space: int
    wifi_state: HardwareState.WiFiState
    wifi_name: str
    wifi_strength: int
    battery_state: HardwareState.BatteryState
    battery_percentage: int
    battery_voltage: int
    battery_current: int
    battery_temperature: int
    battery_remain_capacity: int
    battery_nominal_capacity: int
    battery_use_cycles: int
    battery_remain_time: int
    battery_sn: _containers.RepeatedScalarFieldContainer[str]
    power_state: HardwareState.PowerState
    break_sw_state: HardwareState.BreakSwitchState
    laser_state: HardwareState.LaserState
    cpu_temperature: int
    box_temperature: int
    box_temperature_max: int
    box_temperature_min: int
    box_humidity_max: int
    box_humidity_min: int
    fan_switch_state: bool
    general_io_input: int
    general_io_output: int
    src_hardware_state: SRCHardwareState
    devices: _containers.RepeatedCompositeFieldContainer[Device]
    hardware_state: HardwareState.HState
    hardware_error_code: int
    ip_address: str
    def __init__(self, req_seq: _Optional[int] = ..., cpu_usage: _Optional[int] = ..., memory_usage: _Optional[int] = ..., disk_usage: _Optional[int] = ..., remain_disk_space: _Optional[int] = ..., wifi_state: _Optional[_Union[HardwareState.WiFiState, str]] = ..., wifi_name: _Optional[str] = ..., wifi_strength: _Optional[int] = ..., battery_state: _Optional[_Union[HardwareState.BatteryState, str]] = ..., battery_percentage: _Optional[int] = ..., battery_voltage: _Optional[int] = ..., battery_current: _Optional[int] = ..., battery_temperature: _Optional[int] = ..., battery_remain_capacity: _Optional[int] = ..., battery_nominal_capacity: _Optional[int] = ..., battery_use_cycles: _Optional[int] = ..., battery_remain_time: _Optional[int] = ..., battery_sn: _Optional[_Iterable[str]] = ..., power_state: _Optional[_Union[HardwareState.PowerState, str]] = ..., break_sw_state: _Optional[_Union[HardwareState.BreakSwitchState, str]] = ..., laser_state: _Optional[_Union[HardwareState.LaserState, str]] = ..., cpu_temperature: _Optional[int] = ..., box_temperature: _Optional[int] = ..., box_temperature_max: _Optional[int] = ..., box_temperature_min: _Optional[int] = ..., box_humidity_max: _Optional[int] = ..., box_humidity_min: _Optional[int] = ..., fan_switch_state: bool = ..., general_io_input: _Optional[int] = ..., general_io_output: _Optional[int] = ..., src_hardware_state: _Optional[_Union[SRCHardwareState, _Mapping]] = ..., devices: _Optional[_Iterable[_Union[Device, _Mapping]]] = ..., hardware_state: _Optional[_Union[HardwareState.HState, str]] = ..., hardware_error_code: _Optional[int] = ..., ip_address: _Optional[str] = ...) -> None: ...

class SRCHardwareState(_message.Message):
    __slots__ = ["m1_status_code", "m2_status_code", "m3_status_code", "m4_status_code", "total_power_cycle", "total_poweron_time", "total_mileage", "src_state", "src_state_error_reason"]
    M1_STATUS_CODE_FIELD_NUMBER: _ClassVar[int]
    M2_STATUS_CODE_FIELD_NUMBER: _ClassVar[int]
    M3_STATUS_CODE_FIELD_NUMBER: _ClassVar[int]
    M4_STATUS_CODE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_POWER_CYCLE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_POWERON_TIME_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MILEAGE_FIELD_NUMBER: _ClassVar[int]
    SRC_STATE_FIELD_NUMBER: _ClassVar[int]
    SRC_STATE_ERROR_REASON_FIELD_NUMBER: _ClassVar[int]
    m1_status_code: int
    m2_status_code: int
    m3_status_code: int
    m4_status_code: int
    total_power_cycle: int
    total_poweron_time: int
    total_mileage: int
    src_state: int
    src_state_error_reason: int
    def __init__(self, m1_status_code: _Optional[int] = ..., m2_status_code: _Optional[int] = ..., m3_status_code: _Optional[int] = ..., m4_status_code: _Optional[int] = ..., total_power_cycle: _Optional[int] = ..., total_poweron_time: _Optional[int] = ..., total_mileage: _Optional[int] = ..., src_state: _Optional[int] = ..., src_state_error_reason: _Optional[int] = ...) -> None: ...

class Device(_message.Message):
    __slots__ = ["name", "id", "device_id", "state", "error_code", "serial_no", "model_no", "version_no", "info", "interface_name"]
    class DeviceState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        DEVICE_NONE: _ClassVar[Device.DeviceState]
        DEVICE_OK: _ClassVar[Device.DeviceState]
        DEVICE_OFF: _ClassVar[Device.DeviceState]
        DEVICE_ERROR: _ClassVar[Device.DeviceState]
        DEVICE_ERROR_OPEN_FAILED: _ClassVar[Device.DeviceState]
        DEVICE_ERROR_TIMEOUT: _ClassVar[Device.DeviceState]
    DEVICE_NONE: Device.DeviceState
    DEVICE_OK: Device.DeviceState
    DEVICE_OFF: Device.DeviceState
    DEVICE_ERROR: Device.DeviceState
    DEVICE_ERROR_OPEN_FAILED: Device.DeviceState
    DEVICE_ERROR_TIMEOUT: Device.DeviceState
    NAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    SERIAL_NO_FIELD_NUMBER: _ClassVar[int]
    MODEL_NO_FIELD_NUMBER: _ClassVar[int]
    VERSION_NO_FIELD_NUMBER: _ClassVar[int]
    INFO_FIELD_NUMBER: _ClassVar[int]
    INTERFACE_NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    id: int
    device_id: str
    state: Device.DeviceState
    error_code: int
    serial_no: str
    model_no: str
    version_no: str
    info: str
    interface_name: str
    def __init__(self, name: _Optional[str] = ..., id: _Optional[int] = ..., device_id: _Optional[str] = ..., state: _Optional[_Union[Device.DeviceState, str]] = ..., error_code: _Optional[int] = ..., serial_no: _Optional[str] = ..., model_no: _Optional[str] = ..., version_no: _Optional[str] = ..., info: _Optional[str] = ..., interface_name: _Optional[str] = ...) -> None: ...

class LmkMatchInfo(_message.Message):
    __slots__ = ["x", "y", "yaw", "lmk_type", "is_matched"]
    class LmkMatchType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NONE: _ClassVar[LmkMatchInfo.LmkMatchType]
        TYPE_FLAT: _ClassVar[LmkMatchInfo.LmkMatchType]
        TYPE_CYLINDER: _ClassVar[LmkMatchInfo.LmkMatchType]
        TYPE_LINE_LMK: _ClassVar[LmkMatchInfo.LmkMatchType]
        TYPE_CORNER_LMK: _ClassVar[LmkMatchInfo.LmkMatchType]
        TYPE_NARROW_LMK: _ClassVar[LmkMatchInfo.LmkMatchType]
        TYPE_MIDDLE_CYLINDER_LMK: _ClassVar[LmkMatchInfo.LmkMatchType]
        TYPE_LARGE_CYLINDER_LMK: _ClassVar[LmkMatchInfo.LmkMatchType]
        TYPE_GENERAL_LMK: _ClassVar[LmkMatchInfo.LmkMatchType]
    NONE: LmkMatchInfo.LmkMatchType
    TYPE_FLAT: LmkMatchInfo.LmkMatchType
    TYPE_CYLINDER: LmkMatchInfo.LmkMatchType
    TYPE_LINE_LMK: LmkMatchInfo.LmkMatchType
    TYPE_CORNER_LMK: LmkMatchInfo.LmkMatchType
    TYPE_NARROW_LMK: LmkMatchInfo.LmkMatchType
    TYPE_MIDDLE_CYLINDER_LMK: LmkMatchInfo.LmkMatchType
    TYPE_LARGE_CYLINDER_LMK: LmkMatchInfo.LmkMatchType
    TYPE_GENERAL_LMK: LmkMatchInfo.LmkMatchType
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    YAW_FIELD_NUMBER: _ClassVar[int]
    LMK_TYPE_FIELD_NUMBER: _ClassVar[int]
    IS_MATCHED_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    yaw: int
    lmk_type: LmkMatchInfo.LmkMatchType
    is_matched: bool
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ..., yaw: _Optional[int] = ..., lmk_type: _Optional[_Union[LmkMatchInfo.LmkMatchType, str]] = ..., is_matched: bool = ...) -> None: ...

class SensorLaserPoints(_message.Message):
    __slots__ = ["sensor_name", "xs", "ys", "zs", "reliabilitys", "sensor_uuid"]
    SENSOR_NAME_FIELD_NUMBER: _ClassVar[int]
    XS_FIELD_NUMBER: _ClassVar[int]
    YS_FIELD_NUMBER: _ClassVar[int]
    ZS_FIELD_NUMBER: _ClassVar[int]
    RELIABILITYS_FIELD_NUMBER: _ClassVar[int]
    SENSOR_UUID_FIELD_NUMBER: _ClassVar[int]
    sensor_name: str
    xs: _containers.RepeatedScalarFieldContainer[int]
    ys: _containers.RepeatedScalarFieldContainer[int]
    zs: _containers.RepeatedScalarFieldContainer[int]
    reliabilitys: _containers.RepeatedScalarFieldContainer[int]
    sensor_uuid: int
    def __init__(self, sensor_name: _Optional[str] = ..., xs: _Optional[_Iterable[int]] = ..., ys: _Optional[_Iterable[int]] = ..., zs: _Optional[_Iterable[int]] = ..., reliabilitys: _Optional[_Iterable[int]] = ..., sensor_uuid: _Optional[int] = ...) -> None: ...

class ObaPoint(_message.Message):
    __slots__ = ["level", "pose"]
    class Level(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NONE: _ClassVar[ObaPoint.Level]
        KEY: _ClassVar[ObaPoint.Level]
        SLOW: _ClassVar[ObaPoint.Level]
        STOP: _ClassVar[ObaPoint.Level]
    NONE: ObaPoint.Level
    KEY: ObaPoint.Level
    SLOW: ObaPoint.Level
    STOP: ObaPoint.Level
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    POSE_FIELD_NUMBER: _ClassVar[int]
    level: ObaPoint.Level
    pose: Pose
    def __init__(self, level: _Optional[_Union[ObaPoint.Level, str]] = ..., pose: _Optional[_Union[Pose, _Mapping]] = ...) -> None: ...

class ObaFeaturePoint(_message.Message):
    __slots__ = ["sensor_uuid", "oba_points"]
    SENSOR_UUID_FIELD_NUMBER: _ClassVar[int]
    OBA_POINTS_FIELD_NUMBER: _ClassVar[int]
    sensor_uuid: int
    oba_points: _containers.RepeatedCompositeFieldContainer[ObaPoint]
    def __init__(self, sensor_uuid: _Optional[int] = ..., oba_points: _Optional[_Iterable[_Union[ObaPoint, _Mapping]]] = ...) -> None: ...

class ObaPointInfo(_message.Message):
    __slots__ = ["oba_class_name", "oba_feature_points"]
    class ObaClassName(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NONE: _ClassVar[ObaPointInfo.ObaClassName]
        PALLET: _ClassVar[ObaPointInfo.ObaClassName]
        PERSON: _ClassVar[ObaPointInfo.ObaClassName]
        AMR: _ClassVar[ObaPointInfo.ObaClassName]
        FORKLIFT: _ClassVar[ObaPointInfo.ObaClassName]
        OTHERS: _ClassVar[ObaPointInfo.ObaClassName]
    NONE: ObaPointInfo.ObaClassName
    PALLET: ObaPointInfo.ObaClassName
    PERSON: ObaPointInfo.ObaClassName
    AMR: ObaPointInfo.ObaClassName
    FORKLIFT: ObaPointInfo.ObaClassName
    OTHERS: ObaPointInfo.ObaClassName
    OBA_CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
    OBA_FEATURE_POINTS_FIELD_NUMBER: _ClassVar[int]
    oba_class_name: ObaPointInfo.ObaClassName
    oba_feature_points: _containers.RepeatedCompositeFieldContainer[ObaFeaturePoint]
    def __init__(self, oba_class_name: _Optional[_Union[ObaPointInfo.ObaClassName, str]] = ..., oba_feature_points: _Optional[_Iterable[_Union[ObaFeaturePoint, _Mapping]]] = ...) -> None: ...

class VehicleObaInfo(_message.Message):
    __slots__ = ["base_model_pose", "base_model_info", "nav_stop_distance", "nav_slow_distance", "nav_backward_stop_distance", "nav_backward_slow_distance", "nav_stop_left_width_offset", "nav_stop_right_width_offset", "nav_slow_width_offset", "nav_stop_forward_offset"]
    BASE_MODEL_POSE_FIELD_NUMBER: _ClassVar[int]
    BASE_MODEL_INFO_FIELD_NUMBER: _ClassVar[int]
    NAV_STOP_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    NAV_SLOW_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    NAV_BACKWARD_STOP_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    NAV_BACKWARD_SLOW_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    NAV_STOP_LEFT_WIDTH_OFFSET_FIELD_NUMBER: _ClassVar[int]
    NAV_STOP_RIGHT_WIDTH_OFFSET_FIELD_NUMBER: _ClassVar[int]
    NAV_SLOW_WIDTH_OFFSET_FIELD_NUMBER: _ClassVar[int]
    NAV_STOP_FORWARD_OFFSET_FIELD_NUMBER: _ClassVar[int]
    base_model_pose: Pose
    base_model_info: ObstacleModelInfo
    nav_stop_distance: float
    nav_slow_distance: float
    nav_backward_stop_distance: float
    nav_backward_slow_distance: float
    nav_stop_left_width_offset: float
    nav_stop_right_width_offset: float
    nav_slow_width_offset: float
    nav_stop_forward_offset: float
    def __init__(self, base_model_pose: _Optional[_Union[Pose, _Mapping]] = ..., base_model_info: _Optional[_Union[ObstacleModelInfo, _Mapping]] = ..., nav_stop_distance: _Optional[float] = ..., nav_slow_distance: _Optional[float] = ..., nav_backward_stop_distance: _Optional[float] = ..., nav_backward_slow_distance: _Optional[float] = ..., nav_stop_left_width_offset: _Optional[float] = ..., nav_stop_right_width_offset: _Optional[float] = ..., nav_slow_width_offset: _Optional[float] = ..., nav_stop_forward_offset: _Optional[float] = ...) -> None: ...

class LaserPoints(_message.Message):
    __slots__ = ["req_seq", "xs", "ys", "reliabilitys", "xs1", "ys1", "reliabilitys1", "lmks", "ext_laser_points", "oba_laser_points", "loc_laser_points", "oba_point_infos", "vehicle_oba_info", "ext_laser_3d_points"]
    REQ_SEQ_FIELD_NUMBER: _ClassVar[int]
    XS_FIELD_NUMBER: _ClassVar[int]
    YS_FIELD_NUMBER: _ClassVar[int]
    RELIABILITYS_FIELD_NUMBER: _ClassVar[int]
    XS1_FIELD_NUMBER: _ClassVar[int]
    YS1_FIELD_NUMBER: _ClassVar[int]
    RELIABILITYS1_FIELD_NUMBER: _ClassVar[int]
    LMKS_FIELD_NUMBER: _ClassVar[int]
    EXT_LASER_POINTS_FIELD_NUMBER: _ClassVar[int]
    OBA_LASER_POINTS_FIELD_NUMBER: _ClassVar[int]
    LOC_LASER_POINTS_FIELD_NUMBER: _ClassVar[int]
    OBA_POINT_INFOS_FIELD_NUMBER: _ClassVar[int]
    VEHICLE_OBA_INFO_FIELD_NUMBER: _ClassVar[int]
    EXT_LASER_3D_POINTS_FIELD_NUMBER: _ClassVar[int]
    req_seq: int
    xs: _containers.RepeatedScalarFieldContainer[int]
    ys: _containers.RepeatedScalarFieldContainer[int]
    reliabilitys: _containers.RepeatedScalarFieldContainer[int]
    xs1: _containers.RepeatedScalarFieldContainer[int]
    ys1: _containers.RepeatedScalarFieldContainer[int]
    reliabilitys1: _containers.RepeatedScalarFieldContainer[int]
    lmks: _containers.RepeatedCompositeFieldContainer[LmkMatchInfo]
    ext_laser_points: _containers.RepeatedCompositeFieldContainer[SensorLaserPoints]
    oba_laser_points: _containers.RepeatedCompositeFieldContainer[SensorLaserPoints]
    loc_laser_points: _containers.RepeatedCompositeFieldContainer[SensorLaserPoints]
    oba_point_infos: _containers.RepeatedCompositeFieldContainer[ObaPointInfo]
    vehicle_oba_info: VehicleObaInfo
    ext_laser_3d_points: _containers.RepeatedCompositeFieldContainer[SensorLaserPoints]
    def __init__(self, req_seq: _Optional[int] = ..., xs: _Optional[_Iterable[int]] = ..., ys: _Optional[_Iterable[int]] = ..., reliabilitys: _Optional[_Iterable[int]] = ..., xs1: _Optional[_Iterable[int]] = ..., ys1: _Optional[_Iterable[int]] = ..., reliabilitys1: _Optional[_Iterable[int]] = ..., lmks: _Optional[_Iterable[_Union[LmkMatchInfo, _Mapping]]] = ..., ext_laser_points: _Optional[_Iterable[_Union[SensorLaserPoints, _Mapping]]] = ..., oba_laser_points: _Optional[_Iterable[_Union[SensorLaserPoints, _Mapping]]] = ..., loc_laser_points: _Optional[_Iterable[_Union[SensorLaserPoints, _Mapping]]] = ..., oba_point_infos: _Optional[_Iterable[_Union[ObaPointInfo, _Mapping]]] = ..., vehicle_oba_info: _Optional[_Union[VehicleObaInfo, _Mapping]] = ..., ext_laser_3d_points: _Optional[_Iterable[_Union[SensorLaserPoints, _Mapping]]] = ...) -> None: ...

class Point(_message.Message):
    __slots__ = ["x", "y"]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ...) -> None: ...

class Polygon(_message.Message):
    __slots__ = ["vertexs"]
    VERTEXS_FIELD_NUMBER: _ClassVar[int]
    vertexs: _containers.RepeatedCompositeFieldContainer[Point]
    def __init__(self, vertexs: _Optional[_Iterable[_Union[Point, _Mapping]]] = ...) -> None: ...

class CommonPosesInfo(_message.Message):
    __slots__ = ["type", "car_simulate_poses", "sensor_name", "oba_model_info"]
    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NONE: _ClassVar[CommonPosesInfo.Type]
        AVOID_OBSTACLE: _ClassVar[CommonPosesInfo.Type]
    NONE: CommonPosesInfo.Type
    AVOID_OBSTACLE: CommonPosesInfo.Type
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CAR_SIMULATE_POSES_FIELD_NUMBER: _ClassVar[int]
    SENSOR_NAME_FIELD_NUMBER: _ClassVar[int]
    OBA_MODEL_INFO_FIELD_NUMBER: _ClassVar[int]
    type: CommonPosesInfo.Type
    car_simulate_poses: _containers.RepeatedCompositeFieldContainer[Polygon]
    sensor_name: str
    oba_model_info: _containers.RepeatedCompositeFieldContainer[AvoidancePredictionModel]
    def __init__(self, type: _Optional[_Union[CommonPosesInfo.Type, str]] = ..., car_simulate_poses: _Optional[_Iterable[_Union[Polygon, _Mapping]]] = ..., sensor_name: _Optional[str] = ..., oba_model_info: _Optional[_Iterable[_Union[AvoidancePredictionModel, _Mapping]]] = ...) -> None: ...

class AvoidancePredictionModel(_message.Message):
    __slots__ = ["model_type", "oba_model"]
    class ObaModelType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NONE_TYPE: _ClassVar[AvoidancePredictionModel.ObaModelType]
        VEHICLE_MODEL: _ClassVar[AvoidancePredictionModel.ObaModelType]
        RACK_MODEL: _ClassVar[AvoidancePredictionModel.ObaModelType]
        EXTENDED_MODEL1: _ClassVar[AvoidancePredictionModel.ObaModelType]
    NONE_TYPE: AvoidancePredictionModel.ObaModelType
    VEHICLE_MODEL: AvoidancePredictionModel.ObaModelType
    RACK_MODEL: AvoidancePredictionModel.ObaModelType
    EXTENDED_MODEL1: AvoidancePredictionModel.ObaModelType
    MODEL_TYPE_FIELD_NUMBER: _ClassVar[int]
    OBA_MODEL_FIELD_NUMBER: _ClassVar[int]
    model_type: AvoidancePredictionModel.ObaModelType
    oba_model: _containers.RepeatedCompositeFieldContainer[Polygon]
    def __init__(self, model_type: _Optional[_Union[AvoidancePredictionModel.ObaModelType, str]] = ..., oba_model: _Optional[_Iterable[_Union[Polygon, _Mapping]]] = ...) -> None: ...

class AddressInfo(_message.Message):
    __slots__ = ["req_seq", "ip_address", "mac_address", "nick_name"]
    REQ_SEQ_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    MAC_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    NICK_NAME_FIELD_NUMBER: _ClassVar[int]
    req_seq: int
    ip_address: str
    mac_address: str
    nick_name: str
    def __init__(self, req_seq: _Optional[int] = ..., ip_address: _Optional[str] = ..., mac_address: _Optional[str] = ..., nick_name: _Optional[str] = ...) -> None: ...

class ConnectInfo(_message.Message):
    __slots__ = ["protobuf", "modbus"]
    PROTOBUF_FIELD_NUMBER: _ClassVar[int]
    MODBUS_FIELD_NUMBER: _ClassVar[int]
    protobuf: _containers.RepeatedCompositeFieldContainer[SessionInfo]
    modbus: _containers.RepeatedCompositeFieldContainer[SessionInfo]
    def __init__(self, protobuf: _Optional[_Iterable[_Union[SessionInfo, _Mapping]]] = ..., modbus: _Optional[_Iterable[_Union[SessionInfo, _Mapping]]] = ...) -> None: ...

class SessionInfo(_message.Message):
    __slots__ = ["session_id", "username", "ip_addr", "ip_port"]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    IP_ADDR_FIELD_NUMBER: _ClassVar[int]
    IP_PORT_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    username: str
    ip_addr: str
    ip_port: int
    def __init__(self, session_id: _Optional[int] = ..., username: _Optional[str] = ..., ip_addr: _Optional[str] = ..., ip_port: _Optional[int] = ...) -> None: ...

class FeatureInfos(_message.Message):
    __slots__ = ["pose", "feature_type", "feature_name", "sensor_name", "points"]
    class FeatureType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        TYPE_NONE_CODE: _ClassVar[FeatureInfos.FeatureType]
        TYPE_DM_CODE: _ClassVar[FeatureInfos.FeatureType]
        TYPE_FM_CODE: _ClassVar[FeatureInfos.FeatureType]
        TYPE_SCAN_ANGLE_CODE: _ClassVar[FeatureInfos.FeatureType]
        TYPE_SCAN_LMK_CODE: _ClassVar[FeatureInfos.FeatureType]
    TYPE_NONE_CODE: FeatureInfos.FeatureType
    TYPE_DM_CODE: FeatureInfos.FeatureType
    TYPE_FM_CODE: FeatureInfos.FeatureType
    TYPE_SCAN_ANGLE_CODE: FeatureInfos.FeatureType
    TYPE_SCAN_LMK_CODE: FeatureInfos.FeatureType
    POSE_FIELD_NUMBER: _ClassVar[int]
    FEATURE_TYPE_FIELD_NUMBER: _ClassVar[int]
    FEATURE_NAME_FIELD_NUMBER: _ClassVar[int]
    SENSOR_NAME_FIELD_NUMBER: _ClassVar[int]
    POINTS_FIELD_NUMBER: _ClassVar[int]
    pose: Pose
    feature_type: FeatureInfos.FeatureType
    feature_name: str
    sensor_name: str
    points: _containers.RepeatedCompositeFieldContainer[Point]
    def __init__(self, pose: _Optional[_Union[Pose, _Mapping]] = ..., feature_type: _Optional[_Union[FeatureInfos.FeatureType, str]] = ..., feature_name: _Optional[str] = ..., sensor_name: _Optional[str] = ..., points: _Optional[_Iterable[_Union[Point, _Mapping]]] = ...) -> None: ...

class RegistersValuesResult(_message.Message):
    __slots__ = ["input_registers", "hold_registers", "extend_input_registers", "extend_hold_registers", "coil_registers", "discrete_input_registers"]
    INPUT_REGISTERS_FIELD_NUMBER: _ClassVar[int]
    HOLD_REGISTERS_FIELD_NUMBER: _ClassVar[int]
    EXTEND_INPUT_REGISTERS_FIELD_NUMBER: _ClassVar[int]
    EXTEND_HOLD_REGISTERS_FIELD_NUMBER: _ClassVar[int]
    COIL_REGISTERS_FIELD_NUMBER: _ClassVar[int]
    DISCRETE_INPUT_REGISTERS_FIELD_NUMBER: _ClassVar[int]
    input_registers: _containers.RepeatedScalarFieldContainer[int]
    hold_registers: _containers.RepeatedScalarFieldContainer[int]
    extend_input_registers: _containers.RepeatedScalarFieldContainer[int]
    extend_hold_registers: _containers.RepeatedScalarFieldContainer[int]
    coil_registers: _containers.RepeatedScalarFieldContainer[int]
    discrete_input_registers: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, input_registers: _Optional[_Iterable[int]] = ..., hold_registers: _Optional[_Iterable[int]] = ..., extend_input_registers: _Optional[_Iterable[int]] = ..., extend_hold_registers: _Optional[_Iterable[int]] = ..., coil_registers: _Optional[_Iterable[int]] = ..., discrete_input_registers: _Optional[_Iterable[int]] = ...) -> None: ...

class RedrawInfo(_message.Message):
    __slots__ = ["redraw_info_type", "redraw_result"]
    class RedrawInfoType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NONE: _ClassVar[RedrawInfo.RedrawInfoType]
        START: _ClassVar[RedrawInfo.RedrawInfoType]
        STOP: _ClassVar[RedrawInfo.RedrawInfoType]
        CANCEL: _ClassVar[RedrawInfo.RedrawInfoType]
        STOP_CHECK: _ClassVar[RedrawInfo.RedrawInfoType]
        REDRAW_DATA: _ClassVar[RedrawInfo.RedrawInfoType]
        FINISH: _ClassVar[RedrawInfo.RedrawInfoType]
    NONE: RedrawInfo.RedrawInfoType
    START: RedrawInfo.RedrawInfoType
    STOP: RedrawInfo.RedrawInfoType
    CANCEL: RedrawInfo.RedrawInfoType
    STOP_CHECK: RedrawInfo.RedrawInfoType
    REDRAW_DATA: RedrawInfo.RedrawInfoType
    FINISH: RedrawInfo.RedrawInfoType
    REDRAW_INFO_TYPE_FIELD_NUMBER: _ClassVar[int]
    REDRAW_RESULT_FIELD_NUMBER: _ClassVar[int]
    redraw_info_type: RedrawInfo.RedrawInfoType
    redraw_result: int
    def __init__(self, redraw_info_type: _Optional[_Union[RedrawInfo.RedrawInfoType, str]] = ..., redraw_result: _Optional[int] = ...) -> None: ...

class DebugInfo(_message.Message):
    __slots__ = ["flag", "length", "str_1", "str_2"]
    FLAG_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    STR_1_FIELD_NUMBER: _ClassVar[int]
    STR_2_FIELD_NUMBER: _ClassVar[int]
    flag: bool
    length: int
    str_1: str
    str_2: str
    def __init__(self, flag: bool = ..., length: _Optional[int] = ..., str_1: _Optional[str] = ..., str_2: _Optional[str] = ...) -> None: ...

class ObstacleModelInfo(_message.Message):
    __slots__ = ["length", "width", "up_height", "down_height"]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    UP_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    DOWN_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    length: float
    width: float
    up_height: float
    down_height: float
    def __init__(self, length: _Optional[float] = ..., width: _Optional[float] = ..., up_height: _Optional[float] = ..., down_height: _Optional[float] = ...) -> None: ...

class CameraMetaInfo(_message.Message):
    __slots__ = ["path", "width", "height", "direction", "timestamp_us"]
    PATH_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_US_FIELD_NUMBER: _ClassVar[int]
    path: str
    width: int
    height: int
    direction: int
    timestamp_us: int
    def __init__(self, path: _Optional[str] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., direction: _Optional[int] = ..., timestamp_us: _Optional[int] = ...) -> None: ...
