import math
import logging

from protocol_adapter.protobuf_wrapper.path import Path, Direction
from protocol_adapter.huawei_model.cargo_info import CargoInfo
from protocol_adapter.huawei_model.charge_info import ChargeInfo
from protocol_adapter.huawei_model.move_task import MoveTask
from protocol_adapter.huawei_model.const import *
from protocol_adapter.huawei_model.const import (
    DetectType,
    get_int_dat,
)
from protocol_adapter.utils import AngleUtils, GeometryUtils

_logger = logging.getLogger(__name__)


class LinearMoveTask(MoveTask):
    def __init__(self, task_type):
        super().__init__(task_type)

        self.detect_type = DetectType.Default  # 货架探测方式
        self.detect_time = 0  # 货架探测时间(s)

        self.actuator_info = CargoInfo()

    def from_dat(self, dat):
        super().from_dat(dat)

        if self.is_task_type_shelf():
            self.actuator_info = CargoInfo()
            self.actuator_info.from_dat(dat[OBA_END_DAT_INDEX:])
        elif self.is_task_type_shelf_sn_detect():
            self.detect_type = get_int_dat(dat, OBA_END_DAT_INDEX, 2)
            self.detect_time = get_int_dat(dat, OBA_END_DAT_INDEX + 2, 1)

        # 充电任务
        if self.is_charge_task():
            self.charge_info = ChargeInfo()
            self.charge_info.from_dat(dat[OBA_END_DAT_INDEX : OBA_END_DAT_INDEX + 12])

    def calculate_move_path(self, start_pos, any_move=False):
        if (
            self.is_task_linear_move()
            or self.is_task_type_linear_move_after_put_shelf()
            or self.is_task_type_raise_shelf_only()
        ):
            if not any_move:
                return self.calculate_line_path(start_pos)
            else:
                return self.calculate_all_direction_move(start_pos)
        return []

    # 角度单位: 度
    def create_identify_shelf_leg_rotate_path(self, angle):
        _logger.info(f'identify shelf leg rotate path angle {angle:.3f}')
        target_pose = self.get_move_target()
        rotate_path = Path.create_rotate_path(int(math.radians(angle) * 1000))
        rotate_path.sx = target_pose['x']
        rotate_path.ex = rotate_path.sx
        rotate_path.sy = target_pose['y']
        rotate_path.ey = rotate_path.sy
        rotate_path.direction = Direction.SHELF_LEG_IDENTIFY
        return rotate_path

    def calculate_rotate_path_after_raise_shelf(self, start_angle):
        target_angle = AngleUtils.normalize_360(self.get_target_angle() / 1000)
        if AngleUtils.equal_norm(start_angle, target_angle, ANGLE_30):
            return None
        return Path.create_rotate_path(int(math.radians(target_angle) * 1000))

    def get_distance_to_target(self, cur_pos):
        """获取小车当前位置到目标站点的距离偏移"""
        target_pose = self.get_move_target()
        return GeometryUtils.calculate_distance(
            cur_pos['x'], cur_pos['y'], target_pose['x'], target_pose['y']
        )

    def calculate_adjust_rotate_path(self, cur_pos):
        """顶升后，将小车方向调整到目标角度方向（开同步旋转）"""
        dest_angle = self.move_target.angle / 1000.0
        cur_angle = cur_pos['angle'] / 1000.0
        _logger.debug(f'adjust check: angle offset(deg) {cur_angle:.1f} -> {dest_angle:.1f}')
        # 调整角度大于 5 度且小车不能转的时候，不做调整
        if (
            AngleUtils.delta_norm(cur_angle, dest_angle) > 5
            and not self.is_allow_to_rotate_chassis()
        ):
            return []
        end_yaw = math.radians(dest_angle)
        path = Path.create_rotate_path(int(end_yaw * 1000), lock_space=False)
        path.sx = cur_pos['x']
        path.sy = cur_pos['y']
        return [path]

    def calculate_adjust_line_path(self, cur_pos):
        """判断当前位置是否需要直线路径调整，判断逻辑:
        比较小车当前位置与目标站点的距离偏差：
        1. 小于MIN阀值偏差时，可能是定位漂移(定位精度约2cm)，不需要调整
        2. 大于MAX阀值偏差时，偏差过大，不应该调整

        直线调整的方向保证与小车当前方向一致（不改变角度），调整距离则是投影长度
        """
        target_pose = self.get_move_target()

        distance = GeometryUtils.calculate_distance(
            cur_pos['x'], cur_pos['y'], target_pose['x'], target_pose['y']
        )
        _logger.debug(f'adjust check: distance offset {distance:.3f} mm')
        if (
            distance < RAISE_SHELF_MIN_PATH_LENGTH_THRESHOLD
            or distance > RAISE_SHELF_MAX_PATH_LENGTH_THRESHOLD
        ):
            return []

        cur_angle_90_base = cur_pos['angle'] / 1000.0
        cur_vc_x = math.cos(math.radians(cur_angle_90_base))
        cur_vc_y = math.sin(math.radians(cur_angle_90_base))
        target_vc_x = target_pose['x'] - cur_pos['x']
        target_vc_y = target_pose['y'] - cur_pos['y']
        # 到目标点的直线向量在小车当前方向的投影长度（尺寸单位 mm），根据正负判断方向
        cur_dot = cur_vc_x * target_vc_x + cur_vc_y * target_vc_y

        direct = Direction.Forward
        if cur_dot < 0:
            direct = Direction.BackForward
        dest_pos_x = int(cur_pos['x'] + cur_vc_x * cur_dot)
        dest_pos_y = int(cur_pos['y'] + cur_vc_y * cur_dot)
        path = Path.create_line_path(
            cur_pos['x'], cur_pos['y'], dest_pos_x, dest_pos_y, direct, limit_v=10
        )
        return [path]

    # 计算导航路径, 参数单位dest_x,dest_y: mm
    # dest_angle: 角度　* 1000
    # is_backward: 是否是后退路径
    def calculate_line_path(self, start_pos):
        # 主要存在以下场景
        # 1、服务端只发目标点坐标，角度不变
        # 2、服务器只发旋转角度，坐标不变
        # 3、服务器只发目标点坐标，但是由于小车与运动路径不在一条直线上，
        # 此时小车先旋转，后沿直线导航到目标点

        if not start_pos:
            _logger.error('calculate path error, cur pos or cur task is none')
            return None

        # 只旋转，不回到路网拓扑点
        if self.is_task_type_raise_shelf_only():
            dest_angle = AngleUtils.normalize_360(self.actuator_info.shelf_angle_at_dest / 1000.0)
            det_1 = AngleUtils.delta_norm(start_pos['angle'] / 1000, dest_angle)
            det_2 = AngleUtils.delta_norm(start_pos['angle'] / 1000, dest_angle + 180)
            # 只考虑平行或垂直,如果当前货架是90度，系统目标是-90度,就认为满足要求
            _logger.info(f'angle det1:{det_1:.3f}, det2:{det_2:.3f}')
            if det_2 < det_1:
                dest_angle = AngleUtils.normalize_360(dest_angle + 180)
            end_yaw = math.radians(dest_angle)
            path = Path.create_rotate_path(int(end_yaw * 1000), lock_space=False)
            path.sx = start_pos['x']
            path.sy = start_pos['y']
            return [path]

        dest_x = self.move_target.x
        dest_y = self.move_target.y
        dest_angle = self.move_target.angle
        is_backward = self.is_start_charge() or self.is_move_backward()

        # 服务端发送旋转路径时，坐标与当前坐标一样
        distance = GeometryUtils.calculate_distance(start_pos['x'], start_pos['y'], dest_x, dest_y)
        cur_angle = AngleUtils.normalize_360(start_pos['angle'] / 1000.0)
        start_angle = cur_angle
        paths = []

        limit_v = self.get_limit_v()
        if self.is_start_charge() and self.is_move_backward():
            limit_v = CHARGE_MOVE_BACK_MAX_SPEED

        # 单独举升货架时，调整位置，根据小车当前角度和直线路径角度确定前进或后退调整
        distance_threshold = SHORT_PATH_LEN
        if self.is_task_type_raise_shelf_only():
            _logger.info(f'raise shelf adjust distance {distance:.3f}mm')
            distance_threshold = RAISE_SHELF_MIN_PATH_LENGTH_THRESHOLD

        angle_threshold = START_LINE_PATH_AGV_THRESHOLD
        if distance > distance_threshold:  # 路径如果过短，不移动,系统可能发下来的距离很小
            # 路径很短时，角度阈值大一点
            if distance < SHORT_PATH_LEN_IN_50CM:
                angle_threshold = START_LINE_PATH_AGV_THRESHOLD_AT_SHORT_PATH

            start_yaw = GeometryUtils.calculate_angle(
                start_pos['x'], start_pos['y'], dest_x, dest_y
            )
            start_angle = AngleUtils.normalize_360(math.degrees(start_yaw))  # 0~360°

            if self.is_task_type_raise_shelf_only() and not AngleUtils.equal_norm(
                cur_angle, start_angle, ANGLE_90
            ):
                is_backward = True

            # 如果是后退路径，则当前角度加上180
            if is_backward:
                start_angle = AngleUtils.normalize_360(start_angle + ANGLE_180)

            # 如果起始角度和当前机器人角度偏差小于阈值,则不加入旋转路径
            # 比较角度前必须归一化
            if not AngleUtils.equal_norm(start_angle, cur_angle, angle_threshold):
                if (
                    AngleUtils.equal_norm(start_angle, cur_angle, ANGLE_75)
                    or self.is_task_type_raise_shelf_only()
                ):
                    is_lock_space = False
                else:
                    is_lock_space = True

                _logger.info(
                    f'Add rotate path, angle: start {start_angle:.3f}, cur {cur_angle:.3f}'
                )
                rotate_path = Path.create_rotate_path(
                    int(math.radians(start_angle) * 1000), lock_space=is_lock_space
                )
                rotate_path.sx = start_pos['x']
                rotate_path.sy = start_pos['y']
                paths.append(rotate_path)

            if is_backward:
                line_path = Path.create_line_path(
                    start_pos['x'],
                    start_pos['y'],
                    dest_x,
                    dest_y,
                    Direction.BackForward,
                    limit_v=limit_v,
                )
            else:
                line_path = Path.create_line_path(
                    start_pos['x'], start_pos['y'], dest_x, dest_y, limit_v=limit_v
                )
            line_path.rotate_angle = int(math.radians(start_angle) * 1000)
            paths.append(line_path)
        else:
            _logger.warning(f'离目标点过近: {distance / 1000.0:.3f}m')

        # _logger.info("start angle " + str(start_angle))

        # 如果终点角度与路径角度小于阈值，则不调整
        end_yaw = math.radians(dest_angle / 1000.0)
        dest_degree = AngleUtils.normalize_360(dest_angle / 1000.0)

        # 只有在举升货架时，才要求精确的角度
        # 正常导航如果小角度也加入旋转路径，会导致移动停顿
        if self.is_task_type_raise_shelf_only():
            angle_threshold = TARGET_ANGLE_THRESHOLD

        _logger.info(f'start_angle: {start_angle:.3f}°, dst_degree: {dest_degree:.3f}°')
        if not AngleUtils.equal_norm(start_angle, dest_degree, angle_threshold):
            # 选择角度大于
            if (
                AngleUtils.equal_norm(start_angle, dest_degree, ANGLE_75)
                or self.is_task_type_raise_shelf_only()
            ):
                is_lock_space = False
            else:
                is_lock_space = True
            path = Path.create_rotate_path(int(end_yaw * 1000), lock_space=is_lock_space)
            path.sx = dest_x
            path.sy = dest_y
            paths.append(path)
            _logger.info(f'add path {path}')

        # 根据这些条件可以判定此时车已经在货架中心,货架摆放或者地图映射存在较大误差,无需移动，直接扫码
        # todo 如果地图映射的误差非常大或者货架摆放误差非常大，进行货架腿识别后即使能正确到达货架中心，ldm也不会发扫码动作，而是直接发移动任务去ldm认为的货架位置，导致agv扫码失败，没有安全隐患
        if self.is_task_type_shelf_sn_detect() and distance <= SHORT_PATH_LEN_DETECT:
            _logger.info('the cur pose is shelf center, need not move again')
            paths = []
        return paths

    def is_path_rotate(self, rotate):
        angle = AngleUtils.normalize_360(math.degrees(rotate / 1000))
        _logger.info(f'angle: {angle:.3f}')
        angle %= 90
        return abs(angle) < 3 or abs(90 - angle) < 3

    def __str__(self):
        result = super().__str__()
        if self.is_task_type_shelf_sn_detect():
            result += f'\n  detect_type: {self.detect_type} detect_time: {self.detect_time}'
        # if self.charge_info is not None:
        #     result += self.charge_info.__str__()
        # if self.actuator_info is not None:
        #     result += self.actuator_info.__str__()
        return result

    def calculate_all_direction_move(self, start_pos):
        """先转到目标角度方向，再保持方向，沿路径移动"""
        paths = []
        dest_x = self.move_target.x
        dest_y = self.move_target.y
        dest_deg = self.move_target.angle / 1000.0
        start_angle = AngleUtils.normalize_360(start_pos['angle'] / 1000.0)
        line_path = Path.create_line_path(
            start_pos['x'],
            start_pos['y'],
            dest_x,
            dest_y,
            limit_v=self.get_limit_v(),
        )
        line_path.update_direction_by_start_angle(start_angle)
        if line_path.length > SHORT_PATH_LEN:
            paths.append(line_path)

        if not AngleUtils.equal_norm(start_angle, dest_deg, 5):
            path = Path.create_rotate_path(int(math.radians(dest_deg) * 1000), lock_space=True)
            paths.append(path)
        return paths
