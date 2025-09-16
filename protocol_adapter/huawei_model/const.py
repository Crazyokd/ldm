from enum import IntEnum


TIMEOUT_1_MIN = 60

PROTOCOL_VERSION = 0x2
PROTOCOL_ALARM_VERSION = 0x1

BYTE_NUM_SHELF_INFO = 60
BYTE_NUM_POINT_INFO = 36

ROLLER_ACTION_NONE = 0xFF
ROLLER_ACTION_STOP = 0x0
ROLLER_ACTION_PUT = 0x1  # 设备把货物送往注塑机
ROLLER_ACTION_FETCH = 0x2  # 设备从注塑机接收货物

ROLLER_DIR_LEFT_OR_FORWARD = 0x0  # 左侧或者前方进行接送动作
ROLLER_DIR_RIGHT_OR_BEHIND = 0x1  # 右侧或者后方进行接送动作

SHELF_ANGLE_PARALLEL_ROBOT = 0
SHELF_ANGLE_VERTICAL_ROBOT = 90

UPLOAD_SHELF_ANGLE_FILTER = 5
SHELF_ANGLE_ADJUST_THRESHOLD = 1

OBA_END_DAT_INDEX = 160
CHARGE_MOVE_BACK_MAX_SPEED = 150

ACTION_RETRY_TIME_GAP = 3

ANGLE_0 = 0
ANGLE_30 = 30
ANGLE_75 = 75
ANGLE_90 = 90
ANGLE_MINUS_90 = -90
ANGLE_180 = 180
ANGLE_MINUS_180 = -180
ANGLE_360 = 360


MAX_RAISE_HEIGHT = 100

# 路径最短距离
MIN_PATH_LENGTH = 1000

# 短路径长度, 4cm
SHORT_PATH_LEN = 40

# 举升货架后是否需要调整到系统目标点坐标的阈值 (长度单位：mm)
RAISE_SHELF_MIN_PATH_LENGTH_THRESHOLD = 30
RAISE_SHELF_MAX_PATH_LENGTH_THRESHOLD = 200

# 最远的路网回归距离
MAX_POSITION_DEVIATION_FOR_NET_REGRESSION_MM = 220

SHORT_PATH_LEN_DETECT = 500

SHORT_PATH_LEN_IN_50CM = 500

# 风险目标点前限速的距离
DISTANCE_TO_LIMIT_V_BEFORE_RISK_TARGET = 1000

# 当前路径准备走完，最后剩余距离阈值
REMAIN_DISTANCE_THRESHOLD = 300

# 允许角度误差,单位°
MAX_DEGREE_THRESHOLD = 25
MAX_DEGREE_THRESHOLD_ROLLER = 3

# 货架旋转角度阈值(阀值内无需锁空间申请)
SHELF_ROTATE_ANGLE_THRESHOLD = 5
# 锁空间微调货架对应的小角度阀值(用于 LockSpaceType.RECT_ROTATE 类型的锁空间检查)
RECT_ROTATE_SMALL_ANGLE_THRESHOLD = 10
# 短距离路径跳过时，不宜跳过角度变化，但角度变化应当也有一个阀值，大于这个阀值需要另外检查
SHORT_PATH_LOCKSPACE_ANGLE_THRESHOLD = 10


# 同步旋转自动矫正时，货架前后角度和移动距离限制
MAX_SHELF_ANGLE_TO_RECOVER_FOR_SYNC_ROTATE = 10
MIN_SHELF_ANGLE_TO_RECOVER_FOR_SYNC_ROTATE = SHELF_ANGLE_ADJUST_THRESHOLD
MAX_MOVE_DISTANCE_FOR_SYNC_ROTATE = 40  # 原地旋转，前后位置应该要在 4cm 内(运动精度好像在1cm内)

# 当前agv角度与发送路径起始角度阈值
START_LINE_PATH_AGV_THRESHOLD = 3
TARGET_ANGLE_THRESHOLD = 2.5
START_LINE_PATH_AGV_THRESHOLD_AT_SHORT_PATH = 10  # 路径很短时阈值设置大一点
ALLOWED_ROTATE_ANGLE_BEFORE_BEZIER = 10  # 贝塞尔前允许的最大旋转角度

# 允许距离误差，单位ｍｍ
MAX_XY_THRESHOLD = 100
MAX_XY_THRESHOLD_ROLLER = 30


class MoveType(IntEnum):
    Forward = 0x0  # 前进
    Backward = 0x1  # 后退
    Forward_Rad = 0x2  # 轴向直线前进
    Backward_Rad = 0x3  # 轴向直线后退
    Forward_Bias = 0x4  # 斜线前进
    Backward_Bias = 0x5  # 斜线后退
    Rotate = 0x6  # 旋转(设备自行计算旋转方向，复杂路径使用)
    Rotate_Clockwise = 0x7  # 顺时针旋转，复杂路径使用
    Rotate_Anticlockwise = 0x8  # 逆时针旋转，复杂路径使用
    Still = 0x09  # 不动


class ChargeFlag(IntEnum):
    Start_Charge = 1
    Stop_Charge = 2
    Restart = 3


class TargetType(IntEnum):
    Normal = 0  # 非储位或充电桩
    Storage = 1  # 储位
    Charge_Pile = 2  # 充电桩
    Elevator = 3  # 电梯


class ShelfTaskState(IntEnum):
    Unknown = 0
    Raise_Top = 1
    Put_Bottom = 2
    Pause = 3
    Processing = 4
    Error = 7


class HMIUserSetState(IntEnum):
    NONE = 0x0
    WAITING_FOR_ELEVATOR = 0x1  # 等待电梯
    DISINGECTING = 0x2  # 正在消毒
    FMS_DISCONNECTED = 0x3  # 调度系统掉线
    WHERE_AM_I = 0x4  # 寻找机器人
    IN_TRAFFIC_CONTROL_ = 0x5  # 交通管制中


# 探测控制任务的探测类型
class DetectType(IntEnum):
    Default = 0x0  # 开货码灯扫码 超时扫不到报完成
    NotFoundWarning = 0x1  # 开货码灯扫码 超时扫不到一直扫描并产生货架不识别告警
    QRCodeRefine = 0x2  # 开货码灯扫码 并进行"货架二维码标定”


class LockSpaceRspError(IntEnum):
    SUCCESS = 0x0  # 成功
    FAILED_TMP_LOCKED = 0x1  # 暂时失败，待锁的区域已被其它小车锁住或者有其它小车
    FAILED_TMP_ROBOT = 0x2  # 暂时失败，在偏移格空车旋转、旋转调整时旁边有机器人导致的失败
    FAILED_PERMANENT_INPUT_PARAMS = 0x3  # 永久失败，输入参数不正确
    FAILED_PERMANENT_POSITION = 0x4  # 永久失败，申请锁定处理的位置与当前位置不一致
    FAILED_PERMANENT_INTERNAL_PARAMS = 0x5  # 永久失败，内部参数有误，如锁格申请参数或地图参数不对
    FAILED_PERMANENT_AREA_NO_ROTATE = 0x6  # 永久失败，不在旋转区
    FAILED_PERMANENT_MAP_NOT_ALLOWED = (
        0x7  # 永久失败，地图不支持，如电梯内申请旋转、后退，带货架旋转申请周围有固定障碍物
    )
    # ... 协议文档之外，另外还有 8-29，暂未列出


"""
调整类型：

1. 顶板小车视作一体，调度不单独考虑顶板角度:
    小车不能转的时候顶板也不该转

    > 具体场景分四种:

    - 空车时: 顶板 -- 小车，顶板小车方向绑定
    - 载货时: 顶板 -- 货架，顶板小车方向解绑，与货架绑定

    - 到地方放货架: 顶板从货架方向回到小车方向
        目标点后，货架小车都不让转（同时货架与小车成90度），下放货架后，顶板不会回零
        (需要通过任务规划规避，或者在附近增加调整站点，让小车去调整站点后执行回零操作)

    - 空车去顶货架: 小车转到货架0度方向再顶升
        在禁止旋转顶板的情况下直接顶升，如果货架方向与小车方向不一致，会报错不顶升
        (南方工厂的角度补偿定制就是在处理这个问题，因为目前载货后顶板角度默认货架角度)

2. 调整类型这里有两层含义：
    小车旋转: 0, 5, 360 (完全不可旋转，小角度，自由旋转)
    顶板旋转: 0, 5, 360 (完全不可旋转，小角度，自由旋转)

    隐含的一层：顶板旋转 == 货架旋转 (载货时)

    - 当前调整类型定义：
        0:  不限制旋转
        1:  小车可小角度转，顶板不能转
        2:  小车不能转，顶板不能转
        3:  小车可以转，顶板不能转 (空车时顶板可以旋转)

        4:  顶板可以转，但小车和顶板不能相对旋转（要转一起转）
        5:  小车可小角度转，顶板可小角度转

    当前日志样本只看到过: 0, 1, 3
    4,5 有具体场景吗
"""


class AdjustType(IntEnum):
    # 货物属性：adjust_type,  ldm 下发的货物信息，涉及两类许可：
    # 1. 货架与小车 是否可以相对旋转 (小车转，货架不转，可旋转分: 10度内, 任意旋转)
    # 2. 货架 是否可以旋转 (可旋转分: 10度内, 任意旋转)
    NO_LIMIT = 0x0  # 不限制
    # 可以小角度相对旋转, 转盘不能转。(可以申请锁空间类型为 LockSpaceType.RECT_ROTATE)
    SMALL_ANGLE_TO_SHELF_NO_ROTATE_EXECUTOR = 0x1
    # 禁止相对旋转, 转盘不能转。(都不可转，不能申请空间，在这干等)
    NO_ANGLE_TO_SHELF_NO_ROTATE_EXECUTOR = 0x2
    # 可以相对旋转, 转盘不能转。(可以申请锁空间类型为 LockSpaceType.RECT_ROTATE)
    NO_ROTATE_EXECUTOR = 0x3
    # 禁止相对旋转, 转盘可以转。(可以申请锁空间类型为 LockSpaceType.SHELF_ROTATE)
    NO_ANGLE_TO_SHELF = 0x4
    # 可以小角度相对旋转, 转盘可以小角度转。(可以申请锁空间类型为 LockSpaceType.RECT_ROTATE)
    SMALL_ANGLE_TO_SHELF = 0x5


class LockSpaceType(IntEnum):
    # 申请锁空间的类型: space_type, 发给 ldm, 告知要锁定的空间类型
    NONE = 0x0  # 未初始化的 space_type, 用于判定是否默认值
    SHELF_ROTATE = 0x1  # 货架旋转申请,带货架旋转(自由旋转，不限角度)
    ADJUST_FORWARD = 0x2  # 设备向前调整，空间锁定申请
    ADJUST_BEHIND = 0x3  # 设备向后调整，空间锁定申请
    NO_PAYLOAD_ROTATE = 0x4  # 空车旋转，空间锁定申请
    RECT_ROTATE = 0x5  # 长方形货架和方形转盘，小车货架下面旋转调整或者旋转托盘

    NO_LIMIT = 0x401  # 自定义, 不限调整
    NO_PERMIT = 0x402  # 自定义, 禁止调整


# 本地记录锁空间原因: lock_type, 异步请求响应后，根据锁定原因和请求结果决定后续处理
REQ_SPACE_NONE = 0x0
REQ_SPACE_MOVE_ROTATE = 0x1  # 导航时旋转锁空间
REQ_SPACE_ROTATE_SHELF_BEFORE_MOVE = 0x2  # 导航前旋转货架
REQ_SPACE_ROTATE_SHELF_AT_DESTINATION = 0x3  # 导航到达目标点后旋转货架
REQ_SPACE_ADJUST_WHEN_RAISE_SHELF = 0x04  # 举升货架前校准


class ShelfType(IntEnum):
    Square = 0  # 正方形货架
    Rectangle = 1  # 长方形货架
    All_Powerful = 2  # 万能货架
    Square_No_Leg = 3  # 正方形无腿货架
    Half_Blind = 5  # 半盲举货架


class ScanPolicy(IntEnum):
    Output_Lower_Power = 0x0  # 接第三方设备，输出低电平
    Output_High_Power = 0x1
    Finish_When_Timeout = 0x2  # 超时报完成
    Warning_When_Timeout = 0x3  # 超时报警告


class ShelfAnglePolicy(IntEnum):
    Ignore = 999000
    Vertical = 777000  # 货架与AGV垂直
    Parallel = 666000  # 货架与AGV平行


class ChargeMaintain(IntEnum):
    ChargeTaskMaintain = 0x0  # 设备收到充电任务，发现电池需要申请充满维护
    DeviceMaintain = 0x1  # DeviceMaintain = 0x1


class ProtocolFormat(IntEnum):
    Binary = 0x0  # 二进制数据
    Json = 0x1  # json字节流


class SmtActionDirection(IntEnum):
    Left = 0x0
    Right = 0x1


# 持续未收到状态应答包则需要重新注册
LOST_CONN_TIME_THRESHOLD = 8

MSG_HEADER_LEN = 32
ALARM_HEADER_LEN = 16
RESPONSE_OKAY = 200
RESPONSE_TRUE = 1
RESPONSE_LEN = 8

BA_LEN_1 = 1
BA_LEN_2 = 2
BA_LEN_4 = 4

SAMPLE_POINT_COUNT = 33


MSG_REQ_REGISTER = 0x1
MSG_RSP_REGISTER = 0x2
MSG_REQ_CFG_UPLOAD_STATUS = 0x100
MSG_RSP_CFG_UPLOAD_STATUS = 0x101
MSG_REQ_CFG_GLOBAL_PRECISION = 0x102
MSG_RSP_CFG_GLOBAL_PRECISION = 0x103
MSG_REQ_CFG_WARN_SERVER = 0x104
MSG_RSP_CFG_WARN_SERVER = 0x105
MSG_REQ_CFG_TIME_SYNC = 0x106
MSG_RSP_CFG_TIME_SYNC = 0x107
MSG_REQ_CFG_MOVEMENT_PARAM = 0x108
MSG_RSP_CFG_MOVEMENT_PARAM = 0x109
MSG_REQ_CFG_TIMEOUT = 0x186
MSG_RSP_CFG_TIMEOUT = 0x187
MSG_REQ_CFG_CAPACITY_SET = 0x10A
MSG_RSP_CFG_CAPACITY_SET = 0x10B
MSG_REQ_DEVICE_ABILITY = 0x200
MSG_RSP_DEVICE_ABILITY = 0x201
MSG_REQ_UPLOAD_ABILITY = 0x202
MSG_RSP_UPLOAD_ABILITY = 0x203
MSG_REQ_CFG_UPLOAD_DMCODE = 0x204
MSG_RSP_CFG_UPLOAD_DMCODE = 0x205
MSG_REQ_UPLOAD_DMCODE = 0x206
MSG_RSP_UPLOAD_DMCODE = 0x207
MSG_REQ_VERSIONS = 0x208
MSG_RSP_VERSIONS = 0x209
MSG_REQ_UPLOAD_VERSIONS = 0x20A
MSG_RSP_UPLOAD_VERSIONS = 0x20B
MSG_REQ_CFG_UPLOAD_BATTERY = 0x210
MSG_RSP_CFG_UPLOAD_BATTERY = 0x211
MSG_REQ_UPLOAD_BATTERY_STATUS = 0x212
MSG_RSP_UPLOAD_BATTERY_STATUS = 0x213
MSG_REQ_UPLOAD_STATE = 0x300
MSG_RSP_UPLOAD_STATE = 0x301
MSG_REQ_NO_PAYLOAD_LINEAR_MOVE = 0x302  # 770
MSG_RSP_NO_PAYLOAD_LINEAR_MOVE = 0x303
MSG_REQ_NO_PAYLOAD_ARC_MOVE = 0x304
MSG_RSP_NO_PAYLOAD_ARC_MOVE = 0x305
MSG_REQ_DETECT_CTRL = 0x306
MSG_RSP_DETECT_CTRL = 0x307
MSG_REQ_CHARGE = 0x308
MSG_RSP_CHARGE = 0x309
MSG_REQ_LINEAR_MOVE_AFTER_RAISE_SHELF = (
    0x30A  # !!!!!!!!举升货架叠加直线移动只是移动任务，并不是举升货架动作任务和移动任务的组合
)
MSG_RSP_LINEAR_MOVE_AFTER_RAISE_SHELF = 0x30B
MSG_REQ_LINEAR_MOVE_AFTER_PUT_SHELF = 0x30C  # !!!!!!下放货架叠加直线移动是下放货架+直线移动的组合
MSG_RSP_LINEAR_MOVE_AFTER_PUT_SHELF = 0x30D
MSG_REQ_ARC_MOVE_AFTER_RAISE_SHELF = 0x30E
MSG_RSP_ARC_MOVE_AFTER_RAISE_SHELF = 0x30F
MSG_REQ_ARC_MOVE_AFTER_PUT_SHELF = 0x310
MSG_RSP_ARC_MOVE_AFTER_PUT_SHELF = 0x311
MSG_REQ_RAISE_SHELF = 0x312  # 单独举升控制
MSG_RSP_RAISE_SHELF = 0x313
MSG_REQ_PUT_SHELF = 0x314  # 单独下放控制
MSG_RSP_PUT_SHELF = 0x315
MSG_REQ_SLAM_NAV = 0x316
MSG_RSP_SLAM_NAV = 0x317
MSG_REQ_CHANGE_MAP = 0x318
MSG_RSP_CHANGE_MAP = 0x319
MSG_REQ_NOTIFY_MAP_CHANGE = 0x31A
MSG_RSP_NOTIFY_MAP_CHANGE = 0x31B
MSG_REQ_SWITCH_NAV_MODE = 0x31E
MSG_RSP_SWITCH_NAV_MODE = 0x31F
MSG_REQ_ROLLER_CTRL = 0x320
MSG_RSP_ROLLER_CTRL = 0x321
MSG_REQ_LINEAR_NO_PAYLOAD_MULTI_PATH_MOVE = 0x322
MSG_RSP_LINEAR_NO_PAYLOAD_MULTI_PATH_MOVE = 0x323
MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF = 0x324
MSG_RSP_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF = 0x325
MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_PUT_SHELF = 0x326
MSG_RSP_LINEAR_MULTI_PATH_MOVE_AFTER_PUT_SHELF = 0x327

MSG_REQ_SHELF_ACTION_FORCE = 0x700
MSG_RSP_SHELF_ACTION_FORCE = 0x701
MSG_REQ_LOCK_SPACE = 0x800
MSG_RSP_LOCK_SPACE = 0x801
MSG_REQ_UNLOCK_SPACE = 0x802
MSG_RSP_UNLOCK_SPACE = 0x803
MSG_REQ_CHARGE_MAINTAIN = 0x804
MSG_RSP_CHARGE_MAINTAIN = 0x805
MSG_REQ_REPLAN_ONLINE = 0x806
MSG_RSP_REPLAN_ONLINE = 0x807
MSG_REQ_PAUSE = 0x900
MSG_RSP_PAUSE = 0x901
MSG_REQ_CONTINUE = 0x902
MSG_RSP_CONTINUE = 0x903
MSG_REQ_CANCEL = 0x904
MSG_RSP_CANCEL = 0x905
MSG_REQ_STOP_MOVE = 0x906
MSG_RSP_STOP_MOVE = 0x907
MSG_REQ_WAIT_RELEASE = 0x500
MSG_RSP_WAIT_RELEASE = 0x501
MSG_REQ_ARM_FORK_LOAD_ACTION = 0x328
MSG_RSP_ARM_LOAD_ACTION = 0x329
MSG_REQ_ARM_FORK_UNLOAD_ACTION = 0x32A
MSG_RSP_ARM_UNLOAD_ACTION = 0x32B

MSG_REQ_HIDDEN_FORK_MULTI_PATH_MOVE = 0x33C
MSG_RSP_HIDDEN_FORK_MULTI_PATH_MOVE = 0x33D
MSG_REQ_HIDDEN_FORK_LOAD_ACTION = 0x33E
MSG_RSP_HIDDEN_FORK_LOAD_ACTION = 0x33F
MSG_REQ_HIDDEN_FORK_UNLOAD_ACTION = 0x340
MSG_RSP_HIDDEN_FORK_UNLOAD_ACTION = 0x341

MSG_REQ_SMT_MULTI_PATH_MOVE = 0x344
MSG_RSP_SMT_MULTI_PATH_MOVE = 0x345
MSG_REQ_SMT_LOAD_ACTION = 0x346
MSG_RSP_SMT_LOAD_ACTION = 0x347
MSG_REQ_SMT_UNLOAD_ACTION = 0x348
MSG_RSP_SMT_UNLOAD_ACTION = 0x349

# 告警协议
REQ_UPLOAD_ALARM = 100
RSP_UPLOAD_ALARM = 101

# 告警大类
ALARM_CATEGORY_1 = 1
ALARM_CATEGORY_3 = 3
ALARM_CATEGORY_5 = 5
ALARM_CATEGORY_6 = 6
ALARM_CATEGORY_7 = 7

# 告警等级
ALARM_GRADE_LOW = 1
ALARM_GRADE_NORMAL = 2
ALARM_GRADE_HIGH = 3
ALARM_GRADE_ERROR = 4

# 故障上报/恢复
ALARM_STATUS_OFF = 0  # 故障恢复
ALARM_STATUS_ON = 1  # 故障上报
ALARM_STATUS_PULSE = 2

# 告警具体类型
# ALARM_CATEGORY_1
ALARM_CODE_NETWORK_ERROR = 3  # 网络不通
ALARM_CODE_LOST_CONNECT = 4  # 与平台失联
ALARM_CODE_NAV_OBA_STOP = 6  # 导航阻塞
ALARM_CODE_SHELF_OFFSET = 16  # 货架歪了
ALARM_CODE_REQ_ROTATE_FAILED_FOREVER = 22  # 申请旋转永久失败

# ALARM_CATEGORY_3
ALARM_CODE_FAIL_CONNECT_CHARGE_PILE = 19  # 充电桩未连接

# ALARM_CATEGORY_5
ALARM_CODE_LEFT_MOTOR_ERROR = 16  # 左电机异常
ALARM_CODE_RIGHT_MOTOR_ERROR = 17  # 右电机异常

# ALARM_CATEGORY_6
ALARM_CODE_HIT = 6  # 撞击异常
ALARM_CODE_NO_RECOGNIZE_SHELF_SN = 20  # 货架未识别
ALARM_CODE_SHELF_SN_MISMATCH = 21  # 货架不匹配

# ALARM_CATEGORY_7
ALARM_CODE_FRONT_HIT = 3  # 前碰撞条
ALARM_CODE_BACK_HIT = 6  # 后碰撞条
ALARM_CODE_EMERGENCY = 7  # 急停警告
ALARM_CODE_DETECT_OBA = 27  # 检测到障碍物

SHELF_FORCE_RAISE = 0x0  # 强制举升货架
SHELF_FORCE_PUT = 0x1  # 强制放下货架

LOCK_SPACE_RESEND_INTERVAL = 1
LOCK_SPACE_RESEND_LIVE_TIME = 3

# 导航方式切换
NAV_FROM_SLAM_TO_DMCODE = 0x0  # slam切换到二维码
NAV_FROM_DMCODE_TO_SLAM = 0x1  # 二维码方式切换到slam

BYTES_ORDER = 'big'


DEVICE_VENDOR_ID = 0xC8
DEVICE_SN = 'MR-Q7-LR100A(H)'

DMCODE_TYPE_ADJUST = 'ZZ'


def get_int_dat(dat, begin, size=2, *, signed=True):
    """从字节流中解析整数"""
    if size <= 0:
        return -1
    ba = dat[begin : begin + size]
    return int.from_bytes(ba, byteorder='big', signed=signed)
