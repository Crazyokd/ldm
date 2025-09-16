from enum import IntEnum


class TaskState(IntEnum):
    NONE = 0  # 无异常
    DONE = 1  # 上报任务完成

    NAV_OFF_PATH = 8  # 异常偏航
    TASK_WRONG_ANGLE = 9  # 任务角度异常

    SHELF_ANGLE_ERROR = 10  # 货架角度异常
    SHELF_OFFSET_ERROR = 11  # 货架偏移距离过远
    LOCK_SPACE_FAILED_TEMP = 12  # 锁空间临时失败
    LOCK_SPACE_FAILED_PERMANENT = 13  # 锁空间永久失败


class TaskType(IntEnum):
    Unknown = 0x0
    No_Payload_Linear_Move = 0x302  # 空车直线运动
    No_Payload_Arc_Move = 0x304  # 空车弧线运动
    Shelf_SN_Detect = 0x306  # 探测货物id
    Charge_Task = 0x308  # 充电任务
    Linear_Move_After_Raise_Shelf = 0x30A  # 举货架叠加载货直线运动
    Linear_Move_After_Put_Shelf = 0x30C  # 下放货架叠加空车直线运动
    Arc_Move_After_Raise_Shelf = 0x30E  # 举升叠加载货弧线运动 782
    Arc_Move_After_Put_Shelf = 0x310  # 下放叠加空车弧线运动
    Raise_Shelf_Action = 0x312  # 举起货架 (786)
    Put_Shelf_Action = 0x314  # 放下货架
    Slam_Nav = 0x316  # slam自主上线控制
    Multi_Path_No_Payload_Move = 0x322  # 空车多段路径移动
    Multi_Path_Move_After_Raise_Shelf = 0x324  # 举货架叠加载货多段路径运动
    Multi_Path_Move_After_Put_Shelf = 0x326  # 下放叠加空车多段路径运动
    Roller_Control = 0x320  # 辊筒控制
    Wait_Release = 0x501
    Arm_Fork_Load_Action = 0x328
    Arm_Fork_Unload_Action = 0x32A
    Smt_Multi_Path_Move = 0x344
    Smt_Load_Action = 0x346
    Smt_Unload_Action = 0x348


class TaskItem(IntEnum):
    Normal = 0x0
    Charge = 0x1
    Change_Map = 0x2
    Shelf_Leg_Identify = 0x39  # 动态识别货架腿
    Storage_Business = 0x100  # 仓储业务
    Storage_Fetch = 0x101  # 移动到仓储取货
    Platform_Put = 0x102  # 搬运货物到工作台
    Storage_Put = 0x103  # 搬运货物到储位
    Entry_Lift = 0x51
    ROLLER_Switch = 0x52  # 精准对接
    Fork_load_Action_Go_DOCK = 0x106  # 叉臂取货对接
    Fork_Load_Action_Go_Back = 0x104  # 叉臂载货退出到等待点
    Fork_Unload_Action_Go_DOCK = 0x107  # 叉臂卸货对接
    Fork_Unload_Action_Go_Back = 0x105  # 叉臂卸货退出到等待点
