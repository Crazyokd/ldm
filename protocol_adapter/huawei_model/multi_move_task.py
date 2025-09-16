import logging

import math
import numpy as np

from protocol_adapter.const import ActuatorIdx
from protocol_adapter.huawei_model.smt_info import SmtInfo
from protocol_adapter.models.task import TaskState, TaskType
from protocol_adapter.huawei_model.bezier import CubicBezier, verify_curvature_is_robot_acceptable
from protocol_adapter.huawei_model.cargo_info import CargoInfo
from protocol_adapter.huawei_model.arm_info import ArmInfo
from protocol_adapter.huawei_model.move_task import MoveTask
from protocol_adapter.huawei_model.point import SimplePoint
from protocol_adapter.huawei_model.const import *
from protocol_adapter.huawei_model.const import (
    MAX_POSITION_DEVIATION_FOR_NET_REGRESSION_MM,
    get_int_dat,
)
from protocol_adapter.huawei_model.bezier import get_point, qprime5
from protocol_adapter.huawei_model.fitCurves import (
    fit_5_bezier_sqlit1,
    fit_5_bezier_sqlit2,
    fitCurveIsometricPara,
)
from protocol_adapter.huawei_model.find_path import dist_point_2_line, dist_point_2_bezier
from protocol_adapter.protobuf_wrapper.path import Path, PathType, Direction
from protocol_adapter.utils import AngleUtils, GeometryUtils

_logger = logging.getLogger(__name__)


class MultiMoveTask(MoveTask):
    def __init__(self, task_type):
        super().__init__(task_type)
        # 数据格式: 每组SimplePoint代表ldm下发的一段路径的原始控制点
        # 数据类型：SimplePoint, 没有角度信息的控制点
        # [
        #   [SimplePoint1, SimplePoint2 ...],
        #   [SimplePoint1, SimplePoint2, ...],
        #   ...
        # ]
        self.path_points_groups = []
        self.actuator_info = CargoInfo()

    def from_dat(self, dat):
        super().from_dat(dat)
        paths_param_index = OBA_END_DAT_INDEX
        paths_count = get_int_dat(dat, paths_param_index, 1)
        paths_data_len = get_int_dat(dat, paths_param_index + 2, 2)
        cur_index = paths_param_index + 4
        for group_num in range(0, paths_count):
            path_beg_index = cur_index
            # todo: 没用到的也解析一下
            cur_points_group = []
            limit_v = get_int_dat(dat, cur_index, 2)
            limit_v = min(limit_v, self.get_limit_v())  # 最终限速取子路段限与全路径限速的最小限速
            cur_points_type = get_int_dat(dat, cur_index + 4, 1)
            cur_points_group_len = get_int_dat(dat, cur_index + 5, 1)
            cur_index += 16
            for point_num in range(0, cur_points_group_len):
                point_dat = dat[cur_index : cur_index + 8]
                p = SimplePoint(0, 0, cur_points_type, limit_v)
                p.from_dat(point_dat)
                cur_points_group.append(p)
                cur_index += 8
            cur_index = path_beg_index + 96
            self.path_points_groups.append(cur_points_group)

        maybe_idx = get_int_dat(dat, OBA_END_DAT_INDEX + 484, 2, signed=False)

        if self.is_task_type_shelf():
            _logger.info('is shelf task')
            self.actuator_info = CargoInfo()
            self.actuator_info.from_dat(dat[OBA_END_DAT_INDEX + 484 :])
        elif self.is_task_type_fork_action():
            _logger.info('is fork task')
            self.actuator_info = CargoInfo()
            self.actuator_info.from_dat(dat[OBA_END_DAT_INDEX + 484 :])
        elif self.is_task_type_arm_action():
            self.actuator_info = ArmInfo()
            self.actuator_info.from_dat(dat[OBA_END_DAT_INDEX + 484 :])
            _logger.info(
                f'arm action info({self.actuator_info.action_id}, '
                f'{self.actuator_info.action_param0}, {self.actuator_info.action_param1}'
            )
        elif self.is_task_type_smt() and maybe_idx == ActuatorIdx.SMT:
            self.actuator_info = SmtInfo()
            self.actuator_info.from_dat(dat[OBA_END_DAT_INDEX + 484 :])
        else:
            _logger.info('common move')
            self.actuator_info = CargoInfo()
            self.actuator_info.from_dat(dat[OBA_END_DAT_INDEX + 484 :])

    # start_pos : mm, 1/1000 度, dict
    def calculate_move_path(self, start_pos, need_check_start_pose=True, any_move: bool = False):
        if start_pos is None or self.is_task_type_with_multi_path_move() is False:
            return []
        tmp_start_pose = start_pos.copy()

        dest_angle = self.move_target.angle / 1000.0
        start_angle = AngleUtils.normalize_360(start_pos['angle'] / 1000.0)

        # 当车辆几乎接近目标点时，不应该规划路径，很短的路径会有各种旋转，而且由于定位误差和控制误差，很短的路径也走不准
        distance = GeometryUtils.calculate_distance(
            start_pos['x'], start_pos['y'], self.move_target.x, self.move_target.y
        )
        if distance <= SHORT_PATH_LEN:
            if AngleUtils.equal_norm(start_angle, dest_angle, threshold=5):
                _logger.warning(f'离目标点过近: {distance / 1000.0:.3f}m')
                return []
            else:
                return self.calculate_rotate_paths(start_pos)

        if need_check_start_pose:
            exist_duplicate_path = self.delete_duplicate_paths_group(start_pos)
            # 存在冗余路径或者路径连续，即说明agv正在执行移动任务中，无需校验初始位置,ldm的路径之间严格连续
            need_check_start_pose = not exist_duplicate_path
            tmp_start_pose['angle'] = start_angle
        if len(self.path_points_groups) < 1:
            return []

        if need_check_start_pose:
            _logger.debug(f'need check start pose: {tmp_start_pose}')
            return self.calculate_with_check_start_pose(tmp_start_pose, any_move=any_move)

        paths = []
        for points_group in self.path_points_groups:
            if len(points_group) < 1:
                continue
            if points_group[0].point_type == 0:  # 直线
                paths += self.calculate_line_path(tmp_start_pose, points_group, any_move=any_move)
            elif points_group[0].point_type == 1:  # 贝赛尔
                paths += self.calculate_bezier_path(tmp_start_pose, points_group, any_move=any_move)
            elif points_group[0].point_type == 2:  # 圆弧 (弃用)
                _logger.error('no support arc path, ldm said will not use arc path')
            elif points_group[0].point_type == 3:  # 矩形
                paths += self.calculate_rotate_paths(tmp_start_pose)
            else:
                _logger.info(f'unkown path point_type {points_group[0].point_type}')
        return paths

    # start_pose : mm, 1/1000 度, dict
    # 车在路径上，或者离路径很近，ldm会发的路径组不是从车的位置开始，需要在路径中找到车的位置
    def calculate_with_check_start_pose(self, start_pose, any_move: bool = False):
        min_t, min_idex = self.find_near_path(
            start_pose, accept_diff=MAX_POSITION_DEVIATION_FOR_NET_REGRESSION_MM
        )
        if min_idex == -1:
            _logger.error(
                f'当前机器人距离规划的路径过远，这个任务不能接。{MAX_POSITION_DEVIATION_FOR_NET_REGRESSION_MM}'
            )
            self.state = TaskState.NAV_OFF_PATH
            return []
        paths = []
        path_limit_v = self.path_points_groups[min_idex][0].limit_v

        # 全向移动不走找最远路径的逻辑
        if not any_move:
            path_group_min = self.path_points_groups[min_idex]
            paths += self.fit_path_by_nearst_path(start_pose, min_t, path_group_min, path_limit_v)

        if (
            paths
            and GeometryUtils.calculate_distance(paths[0].sx, paths[0].sy, paths[0].ex, paths[0].ey)
            < 150
        ):
            _logger.info('too short bezier, will replan')
            paths = []
            if min_idex + 1 >= len(self.path_points_groups):
                _logger.info('cant find move path, near dest pose')
                return []
            paths += self.fit_path_by_nearst_path(
                start_pose, 0, self.path_points_groups[min_idex + 1], path_limit_v
            )
        self.delete_duplicate_paths_group(start_pose)
        return paths + self.calculate_move_path(
            start_pose, need_check_start_pose=False, any_move=any_move
        )

    def fit_path_by_nearst_path(self, start_pose, param, path_group, path_limit_v):
        limit_v = min(self.get_limit_v(), path_limit_v)
        if path_group[0].point_type == 0:
            tmp_end_pose = {}
            tmp_end_pose['x'] = path_group[-1].x
            tmp_end_pose['y'] = path_group[-1].y
            tmp_end_pose['angle'] = 0
            print('???', tmp_end_pose)
            return self.calculate_line_path_bt_2_pose(
                start_pose, tmp_end_pose, SHORT_PATH_LEN, limit_v
            )
        elif path_group[0].point_type == 1:
            control_points_raw = np.zeros([len(path_group), 2])
            for i, point in enumerate(path_group):
                control_points_raw[i][0] = point.x
                control_points_raw[i][1] = point.y

            # 同阶拟合
            raw_bezier_len = self.guessCalcBezierLen(control_points_raw)
            tmp_points = control_points_raw.copy()
            for i in range(0, 5):
                tmp_points[i] = get_point(tmp_points[i:], param)
            best_start_yaw = GeometryUtils.calculate_angle(
                tmp_points[0][0],
                tmp_points[0][1],
                tmp_points[1][0],
                tmp_points[1][1],
            )

            # 降阶
            beziers = fit_5_bezier_sqlit2(tmp_points)
            # 防止生成的曲率过大
            for bezier in beziers:
                cubic_bezier = CubicBezier(
                    bezier[0] / 1000.0, bezier[1] / 1000.0, bezier[2] / 1000.0, bezier[3] / 1000.0
                )
                is_acceptable, _, _ = verify_curvature_is_robot_acceptable(cubic_bezier)
                if not is_acceptable:
                    beziers = []
                    break
            if param > 0.5 or raw_bezier_len < 1000 or len(beziers) == 0:
                beziers = fit_5_bezier_sqlit1(tmp_points)
            # 防止生成的曲率过大
            for bezier in beziers:
                cubic_bezier = CubicBezier(
                    bezier[0] / 1000.0, bezier[1] / 1000.0, bezier[2] / 1000.0, bezier[3] / 1000.0
                )
                is_acceptable, _, _ = verify_curvature_is_robot_acceptable(cubic_bezier)
                if not is_acceptable:
                    beziers = []
                    break
            if len(beziers) == 0:
                step = 1 / (SAMPLE_POINT_COUNT - 1)
                t = 0
                sample_points = []
                for i in range(0, SAMPLE_POINT_COUNT):
                    sample_points.append(get_point(tmp_points, t))
                    t += step
                beziers = fitCurveIsometricPara(sample_points)
            paths = []
            direction = Direction.BackForward if self.is_move_backward() else Direction.Forward
            leng = GeometryUtils.calculate_distance(
                beziers[0][0][0],
                beziers[0][0][1],
                beziers[0][1][0],
                beziers[0][1][1],
            )

            # 小圆角贝塞尔的情况下，拟合的贝塞尔的起点角度和贝塞尔上距离车体最近的点的切线近似
            if raw_bezier_len < 1000:
                beziers[0][1][0] = math.cos(best_start_yaw) * leng + beziers[0][0][0]
                beziers[0][1][1] = math.sin(best_start_yaw) * leng + beziers[0][0][1]

            for bezier_points in beziers:
                start_yaw = GeometryUtils.calculate_angle(
                    bezier_points[0][0],
                    bezier_points[0][1],
                    bezier_points[1][0],
                    bezier_points[1][1],
                )
                end_yaw = GeometryUtils.calculate_angle(
                    bezier_points[2][0],
                    bezier_points[2][1],
                    bezier_points[3][0],
                    bezier_points[3][1],
                )
                start_angle = AngleUtils.normalize_360(math.degrees(start_yaw))
                end_angle = AngleUtils.normalize_360(math.degrees(end_yaw))
                if direction == Direction.BackForward:
                    end_angle = AngleUtils.normalize_360(end_angle + 180)
                    start_angle = AngleUtils.normalize_360(start_angle + 180)
                    end_yaw = math.radians(end_angle)
                paths += self.calculate_rotate_path(start_pose, start_angle)
                bezier_path = Path.create_bezier_path(
                    sx=int(bezier_points[0][0]),
                    sy=int(bezier_points[0][1]),
                    cx=int(bezier_points[1][0]),
                    cy=int(bezier_points[1][1]),
                    dx=int(bezier_points[2][0]),
                    dy=int(bezier_points[2][1]),
                    ex=int(bezier_points[3][0]),
                    ey=int(bezier_points[3][1]),
                    direction=direction,
                    limit_v=limit_v,
                )
                bezier_path.rotate_angle = int(end_yaw * 1000)
                paths.append(bezier_path)
                start_pose['x'] = int(bezier_points[3][0])
                start_pose['y'] = int(bezier_points[3][1])
                start_pose['angle'] = end_angle
            return paths
        return []

    def find_near_path(self, start_pose, accept_diff: int):
        if not self.path_points_groups:
            _logger.error('path_points_groups is empty')
            return -1, -1
        p_start = np.array([start_pose['x'], start_pose['y']])
        min_idex = -1
        min_t = -1
        for i in range(0, len(self.path_points_groups)):
            control_points = np.zeros([len(self.path_points_groups[i]), 2])
            for j in range(0, len(control_points)):
                control_points[j][0] = self.path_points_groups[i][j].x
                control_points[j][1] = self.path_points_groups[i][j].y
            dist, t = -1, -1
            if self.path_points_groups[i][0].point_type == 0:
                dist, t = dist_point_2_line(p_start, control_points)
            elif self.path_points_groups[i][0].point_type == 1:
                dist, t = dist_point_2_bezier(p_start, control_points)
            else:
                return -1, -1
            # 不要找离车最短路径的路，要找最靠近终点的，且在可接受的范围内路径，这样就减少了很多旋转路径生成
            if dist < accept_diff and dist >= 0:
                min_idex = i
                min_t = t
        return min_t, min_idex

    # ldm会发送冗余路径，比如先发路径1，2在并执行路径1的过程中发路径2，3，此时需把路径2剔除
    # 并且检测路径是否连续
    def delete_duplicate_paths_group(self, start_pose):
        for valid_idx in range(0, len(self.path_points_groups)):
            if self.path_points_groups[valid_idx][0].point_type == 3:
                continue
            if (
                len(self.path_points_groups[valid_idx]) > 0
                and start_pose['x'] == self.path_points_groups[valid_idx][-1].x
                and start_pose['y'] == self.path_points_groups[valid_idx][-1].y
            ):
                self.path_points_groups = self.path_points_groups[valid_idx + 1 :]
                return True
            if (
                len(self.path_points_groups[valid_idx]) > 0
                and start_pose['x'] == self.path_points_groups[valid_idx][0].x
                and start_pose['y'] == self.path_points_groups[valid_idx][0].y
            ):
                return True
            if (
                len(self.path_points_groups[valid_idx]) > 0
                and self.path_points_groups[valid_idx][0].point_type == 0
                and self.is_in_line(
                    self.path_points_groups[valid_idx][0],
                    self.path_points_groups[valid_idx][-1],
                    start_pose,
                )
            ):
                self.path_points_groups[valid_idx][0].x = start_pose['x']
                self.path_points_groups[valid_idx][0].y = start_pose['y']
                self.path_points_groups = self.path_points_groups[valid_idx:]
                return True
        return False

    def is_in_line(self, pose_s, pose_e, pose):
        det_x1 = pose['x'] - pose_s.x
        det_y2 = pose['y'] - pose_s.y
        det_linex = pose_e.x - pose_s.x
        det_liney = pose_e.y - pose_s.y
        return (
            det_x1 * det_liney == det_y2 * det_linex
            and abs(det_x1) <= abs(det_linex)
            and abs(det_y2) <= abs(det_liney)
        )

    def get_any_move_plan_line(self, pose_start, pose_end, limit_v):
        """生成起点到终点的全向移动路径

        通过构造起始角度与路径，控制最终角度:
            最终角度与路径方向夹角为 90n
            起始角度到最终角度的旋转尽可能小

        1. 转到移动时的朝向
        2. 沿路径保持朝向移动
        3. 转到目标朝向 (正常情况下 1 会转到位，除非路径方向与目标角度有小差值)
        """

        paths = []
        limit_v = min(limit_v, self.get_limit_v())

        distance = GeometryUtils.calculate_distance(
            pose_start['x'], pose_start['y'], pose_end['x'], pose_end['y']
        )
        if distance < SHORT_PATH_LEN:
            _logger.info('ignore short line path')
            return paths

        # 添加全向移动路径
        line_path = Path.create_line_path(
            pose_start['x'],
            pose_start['y'],
            pose_end['x'],
            pose_end['y'],
            limit_v=limit_v,
        )
        line_path.update_direction_by_start_angle(pose_start['angle'])
        paths.append(line_path)

        delta_angle = AngleUtils.delta_norm(pose_start['angle'], pose_end['angle'])
        if delta_angle > 1:
            start_angle = pose_start['angle']
            end_angle = pose_end['angle']
            paths.append(
                Path.create_rotate_path(
                    int(math.radians(end_angle) * 1000), lock_space=delta_angle > 5
                )
            )
        return paths

    def calculate_line_path(self, start_pose, points_group, any_move: bool = False):
        if len(points_group) < 1:
            _logger.info('invalid line contorl points count')
            return []
        paths = []
        line_start_pose = {
            'x': points_group[0].x,
            'y': points_group[0].y,
            'angle': 0,
        }
        line_end_pose = {
            'x': points_group[-1].x,
            'y': points_group[-1].y,
            'angle': 0,
        }
        limit_v = points_group[0].limit_v

        if any_move:
            if (
                line_end_pose['x'] == self.move_target.x
                and line_end_pose['y'] == self.move_target.y
            ):
                target_angle = self.move_target.angle / 1000
            else:
                target_angle = start_pose['angle']

            line_start_pose['x'] = start_pose['x']
            line_start_pose['y'] = start_pose['y']
            line_start_pose['angle'] = target_angle
            line_end_pose['angle'] = target_angle

            paths += self.get_any_move_plan_line(line_start_pose, line_end_pose, limit_v=limit_v)
            start_pose['x'] = line_end_pose['x']
            start_pose['y'] = line_end_pose['y']
            start_pose['angle'] = target_angle
        else:
            paths += self.calculate_line_path_bt_2_pose(
                start_pose, line_end_pose, path_limit_v=limit_v
            )
        return paths

    def calculate_rotate_paths(self, tmp_start_pose):
        dest_angle = self.move_target.angle
        end_yaw = math.radians(dest_angle / 1000.0)
        path = Path.create_rotate_path(int(end_yaw * 1000))
        path.sx = tmp_start_pose['x']
        path.sy = tmp_start_pose['y']
        return [path]

    def calculate_bezier_path(self, start_pose, points_group, any_move: bool = False):
        if len(points_group) < 3:
            _logger.info('invalid bezier contorl points count')
            return []
        paths = []
        end_pose_1 = {}
        end_pose_1['x'] = points_group[0].x
        end_pose_1['y'] = points_group[0].y
        end_pose_1['angle'] = 0  # 不需要用到
        limit_v = min(self.get_limit_v(), points_group[0].limit_v)
        if any_move:  # 贝塞尔全向移动保持相对方向
            end_pose_1['angle'] = start_pose['angle']
            paths += self.get_any_move_plan_line(start_pose, end_pose_1, limit_v)
        else:
            paths += self.calculate_line_path_bt_2_pose(start_pose, end_pose_1, limit_v)

        # 拟合
        control_points = np.zeros((len(points_group), 2))
        for i in range(0, len(control_points)):
            control_points[i][0] = points_group[i].x
            control_points[i][1] = points_group[i].y
        real_end_points = control_points[-1].copy()
        # control_points[-1] = self.get_almost_end_point_from_bezier(control_points[-2], control_points[-1])
        filt_bezier_curves = self.fit_control_point(control_points)
        for bezier_points in filt_bezier_curves:
            if len(bezier_points) != 4:
                return paths

            bezier_path = Path.create_bezier_path(
                sx=int(bezier_points[0][0]),
                sy=int(bezier_points[0][1]),
                cx=int(bezier_points[1][0]),
                cy=int(bezier_points[1][1]),
                dx=int(bezier_points[2][0]),
                dy=int(bezier_points[2][1]),
                ex=int(bezier_points[3][0]),
                ey=int(bezier_points[3][1]),
                limit_v=limit_v,
            )
            bezier_path.update_direction_by_start_angle(start_pose['angle'])
            bezier_path.rotate_angle = int(math.radians(bezier_path.end_facing()) * 1000)
            paths += self.calculate_rotate_path(start_pose, bezier_path.begin_facing())
            paths.append(bezier_path)
            start_pose['x'] = int(bezier_points[3][0])
            start_pose['y'] = int(bezier_points[3][1])
            start_pose['angle'] = bezier_path.end_facing()

        if (
            real_end_points[0] != control_points[-1][0]
            or real_end_points[1] != control_points[-1][1]
        ):
            print(
                'will add short line (%s, %s)-->(%s, %s)'
                % (
                    control_points[-1][0],
                    control_points[-1][1],
                    real_end_points[0],
                    real_end_points[1],
                )
            )
            end_pose_2 = {}
            end_pose_2['x'] = int(real_end_points[0])
            end_pose_2['y'] = int(real_end_points[1])
            end_pose_2['angle'] = 0
            paths += self.calculate_line_path_bt_2_pose(start_pose, end_pose_2, 0, 10)
        return paths

    def fit_control_point(self, control_points):
        beizers = []
        # 如果5阶贝塞尔，优先尝试解线性方程组拟合成两条
        if len(control_points) == 6:
            if self.guessCalcBezierLen(control_points) > 1000:
                beizers = fit_5_bezier_sqlit2(control_points)
            else:
                beizers = fit_5_bezier_sqlit1(control_points)  # 小圆角贝塞尔两条走起来不流畅
            if beizers != []:
                return beizers

        # 1.如果线方程组无解，强制拟合成一条。因为此时已经不容易找到长度不至于过短又能无缝连接的多条贝塞尔
        # 2.如果不是5阶也拟合成一条,因为协议上没有很高阶的贝塞尔
        # 这里用二进制能精准匹配的步长，否则累计误差会变得明显,可能是数据类型使用不当造成的
        step = 1 / (SAMPLE_POINT_COUNT - 1)
        t = 0
        sample_points = []
        for i in range(0, SAMPLE_POINT_COUNT):
            sample_points.append(get_point(control_points, t))
            t += step
        beziers = fitCurveIsometricPara(sample_points[:SAMPLE_POINT_COUNT])
        return beziers

    # start_pose, end_pose: mm, 度, dict
    # start_pose 也是输出变量，用于迭代
    def calculate_line_path_bt_2_pose(
        self, start_pose, end_pose, short_path=SHORT_PATH_LEN, path_limit_v=1000
    ):
        paths = []
        distance = GeometryUtils.calculate_distance(
            start_pose['x'], start_pose['y'], end_pose['x'], end_pose['y']
        )
        distance2 = GeometryUtils.calculate_distance(
            start_pose['x'], start_pose['y'], self.move_target.x, self.move_target.y
        )
        if distance > short_path:
            # 旋转路径
            direction = Direction.Forward
            if self.is_move_backward():
                direction = Direction.BackForward
            limit_v = min(path_limit_v, self.get_limit_v())
            yaw = GeometryUtils.calculate_angle(
                start_pose['x'], start_pose['y'], end_pose['x'], end_pose['y']
            )
            line_angle = AngleUtils.normalize_360(math.degrees(yaw))
            if direction == Direction.BackForward:
                line_angle = AngleUtils.normalize_360(line_angle + 180)
                yaw = math.radians(line_angle)
            if not AngleUtils.equal_norm(
                start_pose['angle'], line_angle, START_LINE_PATH_AGV_THRESHOLD
            ):
                rotate_path = Path.create_rotate_path((int(yaw * 1000)))
                rotate_path.sx = start_pose['x']
                rotate_path.sy = start_pose['y']
                paths.append(rotate_path)
                start_pose['angle'] = line_angle
            line_path = Path.create_line_path(
                start_pose['x'],
                start_pose['y'],
                end_pose['x'],
                end_pose['y'],
                direction,
                limit_v=limit_v,
            )
            line_path.rotate_angle = int(yaw * 1000)
            paths.append(line_path)
        elif distance2 <= short_path:
            dest_angle = self.move_target.angle / 1000.0
            dest_degree = AngleUtils.normalize_360(dest_angle)
            end_yaw = math.radians(dest_angle)
            if not AngleUtils.equal_norm(start_pose['angle'], dest_degree, TARGET_ANGLE_THRESHOLD):
                start_pose['x'] = self.move_target.x
                start_pose['y'] = self.move_target.y
                _logger.info('append rotate line')
                rotate_path = Path.create_rotate_path((int(end_yaw * 1000)))
                rotate_path.sx = start_pose['x']
                rotate_path.sy = start_pose['y']
                paths.append(rotate_path)
                start_pose['angle'] = dest_degree
        start_pose['x'] = end_pose['x']
        start_pose['y'] = end_pose['y']
        return paths

    def calculate_rotate_path(self, start_pose, end_angle, must_rotate=False):
        paths = []
        if (
            AngleUtils.equal_norm(start_pose['angle'], end_angle, START_LINE_PATH_AGV_THRESHOLD)
            is False
            or must_rotate is True
        ):
            print(start_pose['angle'], 'rotate->', end_angle)
            rotate_path = Path.create_rotate_path(int(math.radians(end_angle) * 1000))
            rotate_path.sx = start_pose['x']
            rotate_path.sy = start_pose['y']
            paths.append(rotate_path)
            start_pose['angle'] = end_angle
        return paths

    def get_almost_end_point_from_bezier(self, point_start, point_end):
        ret_point = point_end.copy()
        distance = GeometryUtils.calculate_distance(
            point_start[0], point_start[1], point_end[0], point_end[1]
        )
        if distance < 310:
            return ret_point
        ret_point += 200 / distance * (point_start - point_end)
        return ret_point

    def __str__(self):
        result = super().__str__()
        result += '\n  path_points: [{}]'.format(
            ','.join(self.list_2_str(x) for x in self.path_points_groups)
        )
        return result

    def list_2_str(self, points_list):
        result = '[{}]'.format(','.join([x.__str__() for x in points_list]))
        return result

    def guessCalcBezierLen(self, control_points):
        if len(control_points) != 6:
            return 0

        def remapp(x):  # 将[0,1]变换到[-1,1]
            return 0.5 * x + 0.5

        def getIntegralValue(control_points, t):  # 获取参数t处的被积分函数值
            qprime_value = qprime5(control_points, t)
            return (qprime_value[0] ** 2 + qprime_value[1] ** 2) ** 0.5

        return 0.5 * (
            0.236927 * getIntegralValue(control_points, remapp(-0.90618))
            + 0.236927 * getIntegralValue(control_points, remapp(0.90618))
            + 0.478629 * getIntegralValue(control_points, remapp(-0.538469))
            + 0.478629 * getIntegralValue(control_points, remapp(0.538469))
            + 0.568889 * getIntegralValue(control_points, remapp(0))
        )  # 高斯勒让德近似


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import time

    points_lists_1 = [
        [
            [34701, 30110, 1],
            [34701, 29448, 1],
            [34701, 28900, 1],
            [35502, 28900, 1],
            [36978, 28900, 1],
        ],
        [[36978, 28900, 0], [37915, 28900, 0]],
        [[37915, 28900, 0], [38134, 28900, 0]],
        [
            [38130, 28900, 1],
            [40000, 28100, 1],
            [38434, 29400, 1],
            [39434, 29400, 1],
            [38134, 29800, 1],
            [40000, 29800, 1],
        ],
    ]
    points_lists_1 = [
        [
            [38130, 28900, 1],
            [40000, 28100, 1],
            [38434, 29400, 1],
            [39434, 29400, 1],
            [38134, 29800, 1],
            [40000, 29800, 1],
        ]
    ]
    points_lists_2 = [
        [[34701, 110, 1], [34701, 448, 1], [34701, 900, 1], [36978, 900, 1]],
        [[36978, 900, 0], [37915, 900, 0]],
        [[37915, 900, 0], [38134, 900, 0]],
        [
            [38134, 900, 1],
            [40000, 900, 1],
            [38434, 400, 1],
            [39434, 400, 1],
            [38134, 100, 1],
            [40000, 100, 1],
        ],
    ]
    points_lists_3 = [
        [
            [0.0, 0.0, 1],
            [5.0, 1.0, 1],
            [10.0, 5.0, 1],
            [15.0, 15.0, 1],
            [10.0, 20.0, 1],
            [5.0, 20.0, 1],
            [5.0, 10.0, 1],
            [5.0, 25.0, 1],
            [-10, 0.0, 1],
            [-20, 10, 1],
        ]
    ]
    points_lists_4 = [[[19986, 7656, 1], [20558, 7656, 1], [21130, 7656, 1]]]
    points_lists_5 = [
        [
            [17318, 2713, 1],
            [16696, 2713, 1],
            [16074, 2713, 1],
            [14830, 2713, 1],
            [14830, 3857, 1],
            [14830, 5000, 1],
        ]
    ]
    points_lists_6 = [
        [
            [14830, 6906, 1],
            [14830, 6430, 1],
            [14830, 5953, 1],
            [13143, 5953, 1],
            [13143, 5477, 1],
            [13143, 5000, 1],
        ]
    ]
    points_lists_7 = [
        [[15308, 22504, 0], [12279, 22504, 0]],
        [
            [12279, 22504, 1],
            [12126, 22504, 1],
            [11973, 22504, 1],
            [11666, 22504, 1],
            [11666, 21794, 1],
            [11666, 21084, 1],
        ],
        [[11666, 21084, 0], [11666, 19418, 0]],
    ]
    points_lists_8 = [
        [[18868, 29027, 0], [18868, 25072, 0]],
        [[18868, 25072, 0], [18868, 22928, 0]],
        [
            [18868, 22928, 1],
            [18868, 22427, 1],
            [18868, 21925, 1],
            [19430, 21925, 1],
            [19711, 21925, 1],
            [19992, 21925, 1],
        ],
    ]
    test_list = points_lists_8

    def draw_curve(control_points, curve_colour, point_colour):
        points = np.array([get_point(control_points, t) for t in np.linspace(0, 1, 50)])
        x, y = points[:, 0], points[:, 1]
        plt.plot(x, y, curve_colour)
        for point in control_points:
            plt.plot(*point, point_colour)

    def test_draw_path():
        task = MultiMoveTask(TaskType.Multi_Path_No_Payload_Move)
        start_pose = {}
        for _, points_list in enumerate(test_list):
            points_group = []
            control_points_raw = np.zeros([len(points_list), 2])
            for i, point in enumerate(points_list):
                control_points_raw[i][0] = point[0]
                control_points_raw[i][1] = point[1]
                simple_point = SimplePoint(point[0], point[1], point[2])
                points_group.append(simple_point)
            task.path_points_groups.append(points_group)
            draw_curve(control_points_raw, 'r-', 'r.')
        start_pose['angle'] = -90000
        start_pose['x'] = 18868
        start_pose['y'] = 24928
        task.move_target.x = test_list[-1][-1][0]
        task.move_target.y = test_list[-1][-1][1]
        task.move_target.angle = 0
        t1 = time.time()
        paths = task.calculate_move_path(start_pose)
        t2 = time.time()

        print('cost', t2 - t1, 's')
        for path in paths:
            print(path.__str__())
            if path.type == PathType.PATH_LINE:
                print('will draw line')
                control_points = np.zeros([2, 2])
                control_points[0][0] = path.sx
                control_points[0][1] = path.sy
                control_points[1][0] = path.ex
                control_points[1][1] = path.ey
                print(type(path.sx), 'line')
                # draw_curve(control_points,'y-', 'y.')
            elif path.type == PathType.PATH_BEZIER:
                print('will draw bezier')
                control_points = np.zeros([4, 2])
                control_points[0][0] = path.sx
                control_points[0][1] = path.sy
                control_points[1][0] = path.cx
                control_points[1][1] = path.cy
                control_points[2][0] = path.dx
                control_points[2][1] = path.dy
                control_points[3][0] = path.ex
                control_points[3][1] = path.ey
                print(type(path.sx))
                # draw_curve(control_points,'b-', 'b.')
        plt.show()

    def test_draw_curve():
        for points_list in test_list:
            control_points_raw = np.zeros([len(points_list), 2])
            for i, point in enumerate(points_list):
                control_points_raw[i][0] = point[0]
                control_points_raw[i][1] = point[1]
            draw_curve(control_points_raw, 'r-', 'r.')

            step = 1 / (
                SAMPLE_POINT_COUNT - 1
            )  # 这里用二进制能精准匹配的步长，否则累计误差会变得明显,可能是数据类型使用不当造成的
            t = 0
            sample_points = []
            for i in range(0, SAMPLE_POINT_COUNT):
                sample_points.append(get_point(control_points_raw, t))
                t += step
            time1 = time.time()
            beziers = fitCurveIsometricPara(sample_points)
            time2 = time.time()
            print(time1, ' ', time2, ' ', time2 - time1)
            print(len(beziers))
            for bezier in beziers:
                draw_curve(bezier, 'b-', 'b.')

            bezier = fit_5_bezier_sqlit2(control_points_raw)
            if len(bezier) == 2:
                draw_curve(bezier[0], 'y-', 'y.')
                draw_curve(bezier[1], 'g-', 'g.')
            # bezier = fit_5_bezier_sqlit1(control_points_raw)
            # if len(bezier) == 1:
            #     draw_curve(bezier[0], "y-", "y.")
        plt.show()

    def test_distance():
        for points_list in test_list:
            control_points_raw = np.zeros([len(points_list), 2])
            for i, point in enumerate(points_list):
                control_points_raw[i][0] = point[0]
                control_points_raw[i][1] = point[1]
            draw_curve(control_points_raw, 'r-', 'r.')
            point = get_point(control_points_raw, 0.5)
            p = point.copy()
            plt.plot(*p, 'y.')
            p[0] += 100
            p[1] += 100
            plt.plot(*p, 'b.')
            time1 = time.time()
            dist_tance = dist_point_2_bezier(p, control_points_raw)
            time2 = time.time()
            print(time1, ' ', time2, ' ', time2 - time1)
            print(dist_tance)
            print(point)
        plt.show()

    def test_fit():
        control_points = np.array(
            [
                [17318, 2713],
                [16696, 2713],
                [16074, 2713],
                [14830, 2713],
                [14830, 3857],
                [14830, 5000],
            ]
        )
        control_points = np.array(
            [
                [14830, 6906],
                [14830, 6430],
                [14830, 5953],
                [13143, 5953],
                [13143, 5477],
                [13143, 5000],
            ]
        )
        control_points = np.array(
            [
                [38130.0, 28900.0],
                [40000.0, 28100.0],
                [38434.0, 29400.0],
                [39434.0, 29400.0],
                [38134.0, 29800.0],
                [40000.0, 29800.0],
            ]
        )
        control_points_2 = control_points.copy()
        t = 0.2
        control_points_2[0] = get_point(control_points, t)
        control_points_2[0][0] += 100
        control_points_2[0][1] += 100
        dist, t_fit = dist_point_2_bezier(control_points_2[0], control_points)
        print(dist, ' ', t_fit)
        t = t_fit
        print(len(control_points))
        print(control_points_2[0])
        control_points_2[1] = get_point(control_points[1:], t)
        control_points_2[2] = get_point(control_points[2:], t)
        control_points_2[3] = get_point(control_points[3:], t)
        control_points_2[4] = get_point(control_points[4:], t)
        print('control_points_2 ', control_points_2)
        if t > 0.5:
            beziers = fit_5_bezier_sqlit1(control_points_2)
        else:
            beziers = fit_5_bezier_sqlit2(control_points_2)
        t = 0.27
        print('t ', t_fit)
        cuve_point = get_point(control_points[:5], t)
        print(beziers)
        plt.plot(*cuve_point, 'g.')
        draw_curve(control_points, 'b-', 'b.')
        draw_curve(control_points_2, 'r-', 'r.')
        draw_curve(beziers[0], 'y-', 'y.')
        if len(beziers) > 1:
            draw_curve(beziers[1], 'y-', 'y.')
        plt.show()

    # test_fit()
    # test_distance()
    test_draw_path()
