from enum import IntEnum
from dataclasses import dataclass


class ErrorCode(IntEnum):
    # 启动新移动任务时，任务已经在执行
    MOVEMENT_PRE_TASK_RUNNING = 320003
    # 替换路径时移动任务没有启动,移动任务可能已经结束了，不能继续替换路径，请启动新的移动任务
    PATH_REPLACE_MOVEMENT_TASK_NOT_RUNNING = 330020
    # 只有MOVE_FOLLOW_PATH的移动任务才允许替换路径
    PATH_REPLACE_MOVEMENT_TASK_TYPE_NOT_MOVE_FOLLOW_PATH = 330021
    # 替换路径时，task no不匹配,请检查task no，然后再替换路径
    PATH_REPLACE_MOVEMENT_TASK_NO_MISMATCH = 330023
    # 替换路径时，当前移动任务的路径不止一条,只有当是单条路径的时候才允许替换路径
    PATH_REPLACE_CURRENT_PATH_NUM_IS_NOT_SINGLE = 330024
    # 替换路径时，目标站点已经走过了,请重新规划一条路径去目标站点
    PATH_REPLACE_DEST_POSE_PAST = 330025
    # 替换路径时，paths参数为空
    PATH_REPLACE_PATHS_ARGS_IS_NONE = 330026
    # 替换路径时，paths路径的斜率不一致
    PATH_REPLACE_INCONSISTENT_PATHS_SLOP = 330027


@dataclass(frozen=True)
class ConfigKey:
    SERVER_IP = 'network.server_ip'
    SERVER_PORT = 'network.server_port'
    NICKNAME = 'main.nickname'
    AGV_MODEL = 'main.vehicle_type'
    ACTUATOR_TYPE = 'mc.oasis_assemble'
    RACK_WIDTH = 'rack.max_contour_width'
    RACK_LENGTH = 'rack.max_contour_length'
    STOP_DISTANCE = 'nav.stop_distance'
    STOP_DISTANCE_BACKWARD = 'nav.backward_stop_distance'
    STOP_WIDTH_OFFSET = 'nav.stop_width_offset'
    SLOW_DISTANCE = 'nav.slow_distance'
    SLOW_WIDTH_OFFSET = 'nav.slow_width_offset'


class ActionID(IntEnum):
    SYNC_ROTATE = 4
    DETECT_SVC = 133
    EAC = 192


class DeviceID(IntEnum):
    UP_SVC = 131
    DOWN_SVC = 132
    DOWN_SVC_200 = 137
    UP_SVC_200 = 138


"""
车辆类型分类的配置项：
  main.vehicle_type: str
  mc.oasis_assemble: int
  ac.sr_ac_proj_type_t: int

出于简单起见，需要又一个唯一标志车辆类型的定义，这里选择 device_type；
按目前的逻辑来说，device_type 的导出应当由上述三个配置信息综合处理得到的，
如果有指定 device_type, 由它来反向修改对应配置保持内部一致
"""


class DeviceType(IntEnum):
    """唯一标识设备类型，关联: 执行机构类型, 执行机构索引"""

    NONE = 0x0
    RISER = 0x01
    ROLLER = 0x02
    SMT = 0x08
    AGING = 0x09
    GULF = 0x21
    ALL_DIRECTION = 0x30

    # 0x01 表示举升式AGV设备
    # 0x02 表示滚筒式AGV设备
    # 0x03 表示牵引设备
    # 0x04 表示潜伏叉车
    # 0x10 表示无线充电桩
    # 0x20 表示叉车设备
    # 0x21 表示堆高叉车
    # 0x22 表示搬运叉车
    # 0x23 表示全向叉车
    # 0x30 表示全向泊车
    # 0x50 表示其他外围设备

class DeviceSubType(IntEnum):
    Smt = 0x1
    Aging = 0x2
    # 设备子类型，设备类型为SMT时才生效
    #   0x1: SMT
    #   0x2: 老化工装
    #   0x3: 单板料箱
    #   0x4: RRU
    #   0x5: 托盘工装
    #   0x6: 压板隔热罩


class ActuatorType(IntEnum):
    """执行机构类型"""

    Unknown = 0x0
    Lift = 0x4  # 顶升机构
    Double_Row_Roller = 0x7  # 双排辊筒
    Three_Roller = 0x12  # 三辊筒
    Lift_Rotate = 0x6  # 旋转顶升
    Roller = 0x17  # 辊筒
    Double_Layer_Roller = 0x18  # 双层辊筒
    All_Direction = 0x30  # 全向车
    Smt = 0x90  # SMT (暂定)
    Aging = 0x91  # 老化工装


class ActuatorIdx(IntEnum):
    """HW: 执行机构索引"""

    NONE = 0  # 无附加信息
    ROLLER = 1  # 滚筒设备
    SHELF = 3  # 探测到的货架信息
    GOODS = 4  # 货物信息
    HIDE_FORK = 5  # 隐叉
    ARM = 6  # 机械臂
    GULF = 7  # 叉车
    SMT = 8  # SMT 工装
    AGING = 9  # 老化工装
    CHECK = 249  # 点检状态上报


class NavigationMode(IntEnum):
    DMCODE = 0x0  # 二维码导航
    SLAM = 0x03  # slam导航
