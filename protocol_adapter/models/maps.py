from .state import SystemState

# 动作错误码转系统状态
ActionErrorCode_To_SyetemState = {
    1700: SystemState.ROLL_FAILED,
    1701: SystemState.ROLL_PIO_COMM_FAIL,
    1702: SystemState.ROLL_PIO_COMM_FAIL,
    1704: SystemState.ROLL_PIO_COMM_FAIL,
    1710: SystemState.ROLL_OUT_OF_TIME,
    1711: SystemState.ROLL_INVALID_CMD,
    1712: SystemState.ROLL_OUT_OF_TIME,
    1713: SystemState.WORK_ACTION_FAIL,
    1714: SystemState.WORK_ACTION_FAIL,
    2598: SystemState.ROLL_FAILED,
    2599: SystemState.WORK_ACTION_FAIL,
}
