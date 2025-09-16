import logging

from protocol_adapter.huawei_model.actuator_info import ActuatorInfo
from protocol_adapter.huawei_model.const import (
    get_int_dat,
    AdjustType,
    LockSpaceType,
    ShelfAnglePolicy,
    ShelfType,
)
from protocol_adapter.huawei_model import const

_logger = logging.getLogger(__name__)


class CargoInfo(ActuatorInfo):
    def __init__(self):
        super().__init__()
        # 执行机构信息
        self.actuator_raise_height = 0  # 取、放货动作前需要举升的高度
        self.execute_action_at_x = 0  # 同步执行动作时，执行机构开始执行动作的位姿
        self.execute_action_at_y = 0
        self.execute_action_at_angle = 0

        # 货物信息
        self.shelf_type = ShelfType.Rectangle
        self.raise_precision = 0  # 举货架精度要求，单位mm
        self.adjust_type = 0
        self.raise_height = 0  # 举升高度，单位0.1mm
        self.shelf_angle_policy_at_moving = (
            ShelfAnglePolicy.Ignore  # 货架移动时角度，如果是真实角度，则是相对车头的角度
        )
        self.shelf_angle_at_dest = 0  # 货架方向，单位1/1000 degree
        self.shelf_length = 0  # 单位mm
        self.shelf_width = 0
        self.cargo_weight = 0  # 单位kg
        self.put_precision = 0  # 下放货精度，单位mm

        self.shelf_code_offset_x = 0  # 货码偏移
        self.shelf_code_offset_y = 0
        self.shelf_code_offset_angle = 0

    def __str__(self):
        seq = [
            'id',
            'adjust_type',
            'shelf_angle_at_dest',
            'shelf_angle_policy_at_moving',
            'shelf_type',
            'shelf_length',
            'shelf_width',
            'cargo_weight',
        ]
        seq.extend(x for x in vars(self) if x not in seq)
        return '; '.join(f'{x}: {vars(self)[x]}' for x in seq)

    def from_dat(self, dat):
        if len(dat) < 28:
            _logger.error(f'Invalid cargo data length {len(dat)}')
            return False

        self.actuator_raise_height = get_int_dat(dat, 2, 2)
        self.execute_action_at_x = get_int_dat(dat, 4, 4)
        self.execute_action_at_y = get_int_dat(dat, 8, 4)
        self.execute_action_at_angle = get_int_dat(dat, 12, 4)

        if len(dat) < 100:
            return True

        ba = dat[28:60]
        valid_idx = ba.find(b'\x00')
        self.id = bytes.decode(ba[0:valid_idx], 'utf-8')  # 货架id
        self.shelf_type = get_int_dat(dat, 60, 1)  # 货架类型
        self.raise_precision = get_int_dat(dat, 61, 1)  # 举货架精度
        self.adjust_type = get_int_dat(dat, 62, 1)  # 调整类型
        self.raise_height = get_int_dat(dat, 64, 2)  # 举升高度
        self.shelf_angle_policy_at_moving = get_int_dat(dat, 68, 4)  # 货架移动时角度策略
        self.shelf_angle_at_dest = get_int_dat(dat, 72, 4)  # 货架到达目标位置时的角度
        self.shelf_length = get_int_dat(dat, 76, 4)  # 货架长度
        self.shelf_width = get_int_dat(dat, 80, 4)
        self.cargo_weight = get_int_dat(dat, 84, 2)  # 货物重量
        self.put_precision = get_int_dat(dat, 86, 1)  # 放货架精度
        self.shelf_code_offset_x = get_int_dat(dat, 88, 4)  # 货码偏移
        self.shelf_code_offset_y = get_int_dat(dat, 92, 4)
        self.shelf_code_offset_angle = get_int_dat(dat, 96, 4)

    def get_allowed_space_type(self) -> LockSpaceType:
        space_type_map = {
            AdjustType.NO_LIMIT: LockSpaceType.NO_LIMIT,
            AdjustType.SMALL_ANGLE_TO_SHELF_NO_ROTATE_EXECUTOR: LockSpaceType.RECT_ROTATE,
            AdjustType.NO_ANGLE_TO_SHELF_NO_ROTATE_EXECUTOR: LockSpaceType.NO_PERMIT,
            AdjustType.NO_ROTATE_EXECUTOR: LockSpaceType.RECT_ROTATE,
            AdjustType.NO_ANGLE_TO_SHELF: LockSpaceType.SHELF_ROTATE,
            AdjustType.SMALL_ANGLE_TO_SHELF: LockSpaceType.RECT_ROTATE,
        }

        # 未知的 adjust_type 默认不允许旋转
        return space_type_map.get(AdjustType(self.adjust_type), LockSpaceType.NO_PERMIT)

    def can_rotate_robot_with_shelf(self, space_type: int, rotate_angle: float = 0.0) -> bool:
        """按下发的货架调整策略，判断对给定的锁空间类型，载货时是否需要申请锁空间

        rotate_angle 指需要旋转的角度：
        1. 货架需要旋转的角度(小车与货架一起转)     [目前只涉及这种]
        2. 相对旋转的角度(开同步旋转时，小车需要旋转的角度)
        """

        allowed_space_type = self.get_allowed_space_type()
        _logger.info(
            f'expect space_type:{space_type}, allowed_space_type:{allowed_space_type}, '
            f'rotate_angle:{rotate_angle:.3f}'
        )

        # 载货时，如果给定了旋转角度(rotate_angle>0)，则所有涉及小角度旋转的锁空间类型，都要检查
        # 给定的旋转角度是否在 <小角度>旋转的角度阀值内
        #
        # LockSpaceType.RECT_ROTATE 有两种含义：
        # 1. 货架不动，小车旋转(开同步旋转)
        # 2. 小车带着货架一起小角度旋转 (<10 度)
        # 如果同时有提供旋转角度，就是第二种含义
        if (
            space_type == LockSpaceType.RECT_ROTATE
            and rotate_angle > const.RECT_ROTATE_SMALL_ANGLE_THRESHOLD
        ):
            return False

        return allowed_space_type in (space_type, LockSpaceType.NO_LIMIT)

    def is_allow_to_rotate_chassis(self) -> bool:
        """小车是否可以旋转:
        1. 空车时小车顶板一起转
        2. 载货时小车单独转
        """
        return self.adjust_type in (
            AdjustType.NO_LIMIT,
            AdjustType.NO_ROTATE_EXECUTOR,
            AdjustType.NO_ANGLE_TO_SHELF,
        )

    def is_allow_to_rotate_plate(self, *, load_full: bool) -> bool:
        """顶板是否可以旋转:
        1. 空车时小车顶板一起转
        2. 载货时小车单独转
        """

        allowed_adjust = [
            AdjustType.NO_LIMIT,
            AdjustType.NO_ANGLE_TO_SHELF,
        ]
        if not load_full:
            allowed_adjust.append(AdjustType.NO_ROTATE_EXECUTOR)

        return self.adjust_type in allowed_adjust
