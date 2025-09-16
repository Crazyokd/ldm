import abc
import logging
import math

from protocol_adapter.models.task import TaskType
from protocol_adapter.huawei_model.base_task import BaseTask
from protocol_adapter.huawei_model.cargo_info import CargoInfo
from protocol_adapter.huawei_model.move_target import MoveTarget
from protocol_adapter.huawei_model.obstacle_params import ObstacleParams
from protocol_adapter.huawei_model.roller_info import RollerInfo
from protocol_adapter.huawei_model.const import *
from protocol_adapter.huawei_model.const import (
    DetectType,
    LockSpaceType,
    ShelfAnglePolicy,
    ShelfType,
    get_int_dat,
)
from protocol_adapter.protobuf_wrapper.path import Path
from protocol_adapter.utils import AngleUtils

_logger = logging.getLogger(__name__)


class MoveTask(BaseTask):
    def __init__(self, task_type=TaskType.Unknown):
        super().__init__(task_type)
        self.reserved_byte_10 = 0
        self.is_play_audio = 0  # 是否播放语音
        self.is_light_on = 0  # 是否亮灯
        self.move_target = MoveTarget()  # 目标点信息
        self.oba_params = ObstacleParams()  # 避障参数
        self.detect_type = DetectType.Default  # 探测类型

    def from_dat(self, dat):
        super().from_dat(dat)
        self.reserved_byte_10 = get_int_dat(dat, 10, 1)
        self.is_play_audio = get_int_dat(dat, 12, 1)
        self.is_light_on = get_int_dat(dat, 13, 1)
        self.move_target.from_dat(dat[28:88])
        self.oba_params.from_dat(dat[88:OBA_END_DAT_INDEX])

        current_idx = OBA_END_DAT_INDEX
        if self.is_task_type_roller():
            self.actuator_info = []
            for _ in range(0, 4):
                roller_info = RollerInfo()
                roller_info.from_dat(dat[current_idx : current_idx + 4])
                self.actuator_info.append(roller_info)
                current_idx += 4

    @abc.abstractmethod
    def calculate_move_path(self, start_pos, any_move: bool = False):
        return []

    # 是否使用服务器避障参数
    def is_enable_server_oba_policy(self):
        return self.oba_params.is_enable_server_ctrl_oba_policy()

    # 获取前、后、左、右停止避障距离
    def get_stop_oba_params(self):
        return self.oba_params.get_oba_stop_params()

    # 获取前、后、左、右减速避障距离
    def get_slow_oba_params(self):
        return self.oba_params.get_oba_slow_params()

    def get_limit_v(self):
        if self.move_target:
            return self.move_target.get_limit_v()
        return 0

    def get_valid_roller_dat_number(self):
        if self.is_task_type_roller() is False:
            return 0
        count = 0
        for action_info in self.actuator_info:
            if action_info.is_valid():
                count = count + 1
        return count

    # slam导航时，如果是直线路径，由于可能存在原地旋转偏差，导致斜线移动到达目标点后角度与调度系统目标角度存在一定误差
    # 此时生成一段旋转路径调整到调度系统目标角度
    def get_adjust_rotate_path(self, cur_angle):
        if abs(cur_angle) % ANGLE_90 <= TARGET_ANGLE_THRESHOLD:
            return None

        angle_offset = abs(cur_angle % ANGLE_90 - ANGLE_90)
        if angle_offset <= TARGET_ANGLE_THRESHOLD:
            return None

        _logger.info(f'rotate angle, current robot angle: {cur_angle:.3f}°')
        yaw = math.radians(AngleUtils.to_90n(cur_angle))
        return Path.create_rotate_path(int(yaw * 1000))

    def is_duplicated_task(self, task):
        # 充电任务和停止充电任务可以认为是两个不同任务,即使发送的坐标是相同的
        if task.is_stop_charge():
            return self.is_stop_charge()

        # 任务id不一样，则认为不是相同任务
        task_id, sub_task_id = task.get_task_id()
        if not self.is_same_task_id(task_id, sub_task_id):
            return False

        task_type = task.task_type
        task_detail = task.task_detail
        if (
            task.is_task_linear_move()
            or task.is_task_arc_move()
            or task.is_task_type_with_multi_path_move()
            or task.is_task_raise_shelf()
            or task.is_task_type_arm_action()
            or task.is_task_type_fork_action()
        ):
            is_same = (
                task_type == self.task_type
                and task_detail == self.task_detail
                and self.is_same_target(task)
            )

            # 举升货架叠加运动还需判断货架
            if is_same and task.is_task_type_move_after_raise_shelf():
                is_same = (
                    task.actuator_info.shelf_angle_at_dest == self.actuator_info.shelf_angle_at_dest
                )
            return is_same
        else:  # 动作任务(包括放下货架叠加直线移动)只需要判断移动类型就可以，否则会重复执行动作
            return task_type == self.task_type

    def is_same_target(self, task):
        return (
            abs(self.move_target.x - task.move_target.x) < 20
            and abs(self.move_target.y - task.move_target.y) < 20
            and abs(self.move_target.angle - task.move_target.angle) < 2000
        )

    def get_expected_shelf_angle_to_robot_before_move(self, shelf_angle_to_robot):
        """获取移动前货架与小车的期望相对角度"""
        if not (
            self.is_task_type_linear_move_after_raise_shelf()
            or self.is_task_type_arc_move_after_raise_shelf()
            or self.is_task_type_multi_move_after_raise_shelf()
        ):
            return None

        policy = self.actuator_info.shelf_angle_policy_at_moving
        if policy == ShelfAnglePolicy.Ignore:
            return None

        cur_diff = AngleUtils.normalize_180(shelf_angle_to_robot)  # 当前偏差角度
        dest_diff = 0  # 期望偏差角度

        if policy == ShelfAnglePolicy.Parallel:
            dest_diff = 0 if abs(cur_diff) < 90 else 180
        elif policy == ShelfAnglePolicy.Vertical:
            dest_diff = 90
        else:  # 系统下发了期望偏差角度：ldm 要求货架与小车相差一个角度
            dest_diff = AngleUtils.normalize_180(policy / 1000)

        return dest_diff

    def is_need_rotate_shelf_before_move(self, shelf_angle_to_robot):
        """导航移动前是否需要调整货架(是否需要申请锁空间的调整)"""
        cur_diff = AngleUtils.normalize_180(shelf_angle_to_robot)  # 当前偏差角度
        dest_diff = self.get_expected_shelf_angle_to_robot_before_move(shelf_angle_to_robot)
        if dest_diff is None:
            return False
        return not AngleUtils.equal_norm(cur_diff, dest_diff, SHELF_ROTATE_ANGLE_THRESHOLD)

    def get_shelf_angle_offset_at_destination(self, cur_angle):
        """获取传入的货架角度与货架在终点时期望的角度的偏差

        Args:
            cur_angle: 当前货架的角度方向
        Return:
            float: 当前货架朝向与终点处货架期望朝向的夹角
        """
        shelf_angle_at_dest = self.get_shelf_angle_at_dest()
        if shelf_angle_at_dest == ShelfAnglePolicy.Ignore:
            return 0
        return AngleUtils.delta_norm(cur_angle, shelf_angle_at_dest)

    # 导航到达目标位置后是否需要调整货架
    def is_need_rotate_shelf_at_destination(self, cur_angle):
        angle_offset = self.get_shelf_angle_offset_at_destination(cur_angle)
        return angle_offset > SHELF_ROTATE_ANGLE_THRESHOLD

    def is_allow_to_rotate_with_shelf(self, space_type, rotate_angle: float = 0.0):
        """货架相关任务需要判断是否允许旋转，以确定是否申请锁空间"""
        if not self.is_task_type_shelf() or not self.actuator_info:
            return True
        assert isinstance(self.actuator_info, CargoInfo)
        return self.actuator_info.can_rotate_robot_with_shelf(space_type, rotate_angle=rotate_angle)

    def is_allow_to_rotate_plate(self, *, load_full: bool):
        """顶板是否允许旋转"""
        if not self.is_task_type_shelf() or not self.actuator_info:
            return True
        assert isinstance(self.actuator_info, CargoInfo)
        return self.actuator_info.is_allow_to_rotate_plate(load_full=load_full)

    def is_allow_to_rotate_chassis(self):
        """小车是否允许旋转"""
        if not self.is_task_type_shelf() or not self.actuator_info:
            return True
        assert isinstance(self.actuator_info, CargoInfo)
        return self.actuator_info.is_allow_to_rotate_chassis()

    # 获取导航过程中货架角度（相对于车）
    def get_shelf_angle_at_moving(self):
        result = 0
        if self.is_task_type_shelf():
            policy = self.actuator_info.shelf_angle_policy_at_moving
            if policy == ShelfAnglePolicy.Ignore:
                result = ShelfAnglePolicy.Ignore
            elif policy == ShelfAnglePolicy.Parallel:
                result = SHELF_ANGLE_PARALLEL_ROBOT
            elif policy == ShelfAnglePolicy.Vertical:
                result = SHELF_ANGLE_VERTICAL_ROBOT
            elif AngleUtils.is_90n(policy / 1000):
                # 协议下发的角度是相对货架的角度
                return AngleUtils.normalize_360(policy / 1000)
        return result

    def get_shelf_angle_from_robot(self, shelf_angle, robot_angle):
        return AngleUtils.normalize_360(shelf_angle - robot_angle)

    def get_move_target(self):
        return self.move_target.get_target()

    # 返回的角度值乘以1000倍
    def get_target_angle(self):
        target = self.get_move_target()
        return target['angle']

    # 货架目标角度是否一致
    def is_equal_to_shelf_target_angle(self, angle, threshold=ANGLE_30):
        _logger.info(self.actuator_info)
        if self.actuator_info is None:
            return True

        target_angle = self.get_shelf_angle_at_dest()
        if target_angle == ShelfAnglePolicy.Ignore:
            return True
        return AngleUtils.equal_norm(angle, target_angle, threshold)

    def get_shelf_angle_at_dest(self):
        """货架目标角度任意时，返回特殊值，须特别处理"""
        if self.is_task_type_shelf():
            assert isinstance(self.actuator_info, CargoInfo)
            if self.actuator_info.shelf_angle_at_dest != ShelfAnglePolicy.Ignore:
                return self.actuator_info.shelf_angle_at_dest / 1000

        return ShelfAnglePolicy.Ignore

    def get_shelf_sn_from_task(self):
        if self.is_task_type_shelf():
            return self.actuator_info.id
        return ''

    def is_no_detect_raise(self):
        return (
            (self.is_task_type_move_after_raise_shelf() or self.is_task_type_raise_shelf_only())
            and self.actuator_info
            and self.actuator_info.shelf_type == ShelfType.All_Powerful
        )

    def is_no_sync_rotate_task(self):
        if not self.is_task_type_shelf():
            return True
        return self.actuator_info and self.actuator_info.shelf_type == ShelfType.All_Powerful

    # 货架id是否匹配
    def is_shelf_sn_match(self, shelf_sn):
        if self.is_task_type_raise_shelf_only() is False:
            return False
        return shelf_sn not in ('-', '') and shelf_sn == self.get_shelf_sn_from_task()

    def is_at_target_pos(self, cur_robot_pos, ignore_angle=False):
        cur_angle = AngleUtils.normalize_360(cur_robot_pos['angle'] / 1000.0)
        x = self.move_target.x
        y = self.move_target.y
        max_det_xy = MAX_XY_THRESHOLD
        max_det_angle = MAX_DEGREE_THRESHOLD
        if self.is_task_type_roller():
            max_det_xy = MAX_XY_THRESHOLD_ROLLER
            max_det_angle = MAX_DEGREE_THRESHOLD_ROLLER
        target_angle = AngleUtils.normalize_360(self.move_target.angle / 1000.0)
        if abs(cur_robot_pos['x'] - x) > max_det_xy or abs(cur_robot_pos['y'] - y) > max_det_xy:
            return False
        return ignore_angle or AngleUtils.equal_norm(cur_angle, target_angle, max_det_angle)

    def __str__(self):
        return '\n  '.join(x.__str__() for x in (super(), self.move_target, self.oba_params))
