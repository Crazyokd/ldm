import logging
import math

from protocol_adapter.huawei_model.cargo_info import CargoInfo
from protocol_adapter.huawei_model.move_task import MoveTask
from protocol_adapter.huawei_model.point import Point
from protocol_adapter.huawei_model.const import *
from protocol_adapter.utils import AngleUtils, GeometryUtils
from protocol_adapter.protobuf_wrapper.path import Direction, Path

_logger = logging.getLogger(__name__)

BEZIER_CTRL_POS_THRESHOLD = 100  # 10cm
GOLDEN_SECTION_RATIO = 0.618


class ArcMoveTask(MoveTask):
    def __init__(self, task_type):
        super().__init__(task_type)
        self.path_points = []

    def get_arc_last_point(self):
        if len(self.path_points) <= 0:
            return None
        return self.path_points[len(self.path_points) - 1]

    def from_dat(self, dat):
        super().from_dat(dat)

        arc_param_index = OBA_END_DAT_INDEX
        point_cnt = dat[arc_param_index]
        cur_index = arc_param_index + 4
        for cur_num in range(0, point_cnt):
            point_dat = dat[cur_index : cur_index + BYTE_NUM_POINT_INFO]
            p = Point()
            p.from_dat(point_dat)
            self.path_points.append(p)
            cur_index += BYTE_NUM_POINT_INFO

        if self.is_task_type_shelf():
            self.actuator_info = CargoInfo()
            self.actuator_info.from_dat(dat[OBA_END_DAT_INDEX + 4 + BYTE_NUM_POINT_INFO * 8 :])

    def calculate_move_path(self, start_pos):
        if start_pos is None or self.is_task_arc_move() is False:
            return []
        return self._calculate_bezier_path(start_pos)

    # 判断圆弧路径是否是相同圆弧
    def is_same_arc_points(self, points):
        if len(points) < 2 or len(points) != len(self.path_points):
            return False
        return self.path_points[0].is_equal(points[0]) and self.path_points[
            len(self.path_points) - 1
        ].is_equal(points[len(points) - 1])

    def is_between_arc_points(self, x, y):
        if self.is_task_arc_move() is False:
            return False
        start_pos = self.path_points[0]
        end_pos = self.path_points[-1]
        return (start_pos.x < x < end_pos.x or end_pos.x < x < start_pos.x) and (
            start_pos.y < y < end_pos.y or end_pos.y < y < start_pos.y
        )

    def _calculate_bezier_path(self, cur_pos):
        # 调度系统发的圆弧路径规则
        # 1、还未到圆弧起点位置即提前发了路径
        # 2、圆弧点参数中有两个点，第一个点为圆弧起点,第二个点为圆弧终点，目标点与第二个点连线为圆弧切线
        # 3、算法：以圆弧起点、起点角度（切线）、圆弧终点、终点角度（切线）生成贝塞尔曲线

        path_points = self.path_points
        if len(path_points) <= 1:
            _logger.error('Illegal path points size ' + str(len(path_points)))
            return []

        paths = []

        is_backward = self.is_move_backward()
        if is_backward:
            direction = Direction.BackForward
        else:
            direction = Direction.Forward

        arc_start = {
            'x': path_points[0].x,
            'y': path_points[0].y,
            'angle': path_points[0].angle / 1000,
        }
        arc_end = {
            'x': path_points[-1].x,
            'y': path_points[-1].y,
            'angle': path_points[-1].angle / 1000,
        }

        target_pos = self.get_move_target()
        limit_v = self.get_limit_v()
        cur_angle = AngleUtils.normalize_360(cur_pos['angle'] / 1000)
        distance = GeometryUtils.calculate_distance(
            cur_pos['x'], cur_pos['y'], arc_start['x'], arc_start['y']
        )

        # 路径很短时不要发送短路径，以免报src起始角度偏差过大
        # TODO: zz: 这里距离很短的时候，如果直接跳过，有可能导致角度偏差大于 5 度阀值，
        #   然后会有终点处申请锁空间的逻辑，但这里不一定会给通过
        if distance > SHORT_PATH_LEN:
            # 旋转路径
            yaw = GeometryUtils.calculate_angle(
                cur_pos['x'], cur_pos['y'], arc_start['x'], arc_start['y']
            )

            line_angle = AngleUtils.normalize_360(math.degrees(yaw))
            _logger.info(f'cur_angle: {cur_angle}, line_angle angle: {line_angle}, yaw: {yaw}')
            if not AngleUtils.equal_norm(cur_angle, line_angle, START_LINE_PATH_AGV_THRESHOLD):
                rotate_path = Path.create_rotate_path(int(yaw * 1000))
                rotate_path.sx = cur_pos['x']
                rotate_path.sy = cur_pos['y']
                paths.append(rotate_path)

            # 当前位置和圆弧起点直线路径
            line_path = Path.create_line_path(
                cur_pos['x'],
                cur_pos['y'],
                arc_start['x'],
                arc_start['y'],
                direction,
                limit_v=limit_v,
            )
            line_path.rotate_angle = int(yaw * 1000)
            paths.append(line_path)
            cur_angle = line_angle

        # 直线到贝塞尔切线
        _logger.info('cur_angle: %d, arc_start angle: %d' % (cur_angle, arc_start['angle']))
        if not AngleUtils.equal_norm(cur_angle, arc_start['angle'], START_LINE_PATH_AGV_THRESHOLD):
            rotate_path = Path.create_rotate_path(int(math.radians(arc_start['angle']) * 1000))
            rotate_path.sx = arc_start['x']
            rotate_path.sy = arc_start['y']
            paths.append(rotate_path)

        start_yaw = math.radians(arc_start['angle'])
        end_yaw = math.radians(arc_end['angle'])
        # center_pos = {"x": (arc_start["x"] + arc_end["x"]) / 2, "y": (arc_start["y"] + arc_end["y"]) / 2}
        cx, cy = self._calculate_bezier_ctrl_pos(
            {'x': math.cos(start_yaw), 'y': math.sin(start_yaw)}, arc_start, arc_end
        )
        dx, dy = self._calculate_bezier_ctrl_pos(
            {'x': math.cos(end_yaw), 'y': math.sin(end_yaw)}, arc_end, arc_start
        )

        # 贝塞尔曲线
        bezier_path = Path.create_bezier_path(
            sx=arc_start['x'],
            sy=arc_start['y'],
            cx=cx,
            cy=cy,
            ex=arc_end['x'],
            ey=arc_end['y'],
            dx=dx,
            dy=dy,
            direction=direction,
            limit_v=self.get_arc_max_speed(),
        )
        bezier_path.rotate_angle = int(end_yaw * 1000)
        paths.append(bezier_path)

        # 由于执行贝塞尔路径时，角度偏差角度，因此需要加旋转路径校准
        # paths.append(Path.create_rotate_path(int(math.radians(arc_end["angle"]) * 1000), limit_v=limit_v))

        cur_angle = arc_end['angle']
        distance = GeometryUtils.calculate_distance(
            arc_end['x'], arc_end['y'], target_pos['x'], target_pos['y']
        )
        if distance > SHORT_PATH_LEN:
            # 旋转路径
            yaw = GeometryUtils.calculate_angle(
                arc_end['x'], arc_end['y'], target_pos['x'], target_pos['y']
            )

            line_angle = AngleUtils.normalize_360(math.degrees(yaw))
            if not AngleUtils.equal_norm(cur_angle, line_angle, START_LINE_PATH_AGV_THRESHOLD):
                rotate_path = Path.create_rotate_path(int(yaw * 1000))
                rotate_path.sx = arc_end['x']
                rotate_path.sy = arc_end['y']
                paths.append(rotate_path)

            # 圆弧终点和目标点直线路径
            line_path = Path.create_line_path(
                arc_end['x'],
                arc_end['y'],
                target_pos['x'],
                target_pos['y'],
                direction,
                limit_v=limit_v,
            )
            line_path.rotate_angle = int(math.radians(target_pos['angle'] / 1000) * 1000)
            paths.append(line_path)

        return paths

    # 根据切线和切线外圆弧一点计算圆弧
    def calculate_arc_path_by_end_tangent(self, cur_pos):
        # 调度系统发的圆弧路径规则
        # 1、还未到圆弧起点位置即提前发了路径
        # 2、圆弧点参数中有两个点，第一个点为圆弧起点,第二个点为圆弧终点，目标点与第二个点连线为圆弧切线
        # 3、算法：收到圆弧路径时，生成三段路径一起发给小车
        # 当前车的起点和圆弧起点的直线路径(不考虑旋转)
        # 圆弧路径
        # 圆弧终点和目标点的切线直线路径

        path_points = self.path_points
        if len(path_points) <= 1:
            _logger.error('Illegal path points size ' + str(len(path_points)))
            return []

        paths = list()

        is_backward = self.is_move_backward()
        if is_backward:
            direction = Direction.BackForward
        else:
            direction = Direction.Forward

        arc_start = {
            'x': path_points[0].x,
            'y': path_points[0].y,
            'angle': path_points[0].angle / 1000,
        }
        arc_end = {
            'x': path_points[-1].x,
            'y': path_points[-1].y,
            'angle': path_points[-1].angle / 1000,
        }

        target_pos = self.get_move_target()

        limit_v = self.get_limit_v()

        cur_angle = AngleUtils.normalize_360(cur_pos['angle'] / 1000)

        distance = GeometryUtils.calculate_distance(
            cur_pos['x'], cur_pos['y'], arc_start['x'], arc_start['y']
        )
        # 路径很短时不要发送短路径，以免报src起始角度偏差过大
        if distance > SHORT_PATH_LEN:
            # 旋转路径
            yaw = GeometryUtils.calculate_angle(
                cur_pos['x'], cur_pos['y'], arc_start['x'], arc_start['y']
            )

            line_angle = AngleUtils.normalize_360(math.degrees(yaw))
            if not AngleUtils.equal_norm(cur_angle, line_angle, 5):
                paths.append(Path.create_rotate_path(int(yaw * 1000)))

            # 当前位置和圆弧起点直线路径
            paths.append(
                Path.create_line_path(
                    cur_pos['x'],
                    cur_pos['y'],
                    arc_start['x'],
                    arc_start['y'],
                    direction,
                    limit_v=limit_v,
                )
            )
            cur_angle = line_angle

        # 计算圆弧路径
        x1 = arc_end['x']
        y1 = arc_end['y']

        x2 = arc_start['x']
        y2 = arc_start['y']
        tangent_slope = math.tan(math.radians(arc_end['angle']))
        a = -(x2 - x1) / (y2 - y1)
        b = (pow(x2, 2) + pow(y2, 2) - pow(x1, 2) - pow(y1, 2)) / (2 * (y2 - y1))
        if tangent_slope != float('inf'):
            if tangent_slope == 0:
                cx = x1
                cy = b + (x1 - x2) * cx / (y2 - y1)
            else:
                cx = (x1 + tangent_slope * y1 - tangent_slope * b) / (a * tangent_slope + 1)
                cy = (x1 + tangent_slope * y1 - cx) / tangent_slope

            radius = math.sqrt(pow(x1 - cx, 2) + pow(y1 - cy, 2))
        else:
            # 圆弧切线垂直x轴
            cy = y1
            cx = (b - y1) / a
            radius = math.fabs(cx - x1)

        delta_x1 = x2 - cx
        delta_y1 = y2 - cy
        delta_x2 = x1 - x2
        delta_y2 = y1 - y2
        facing = delta_x1 * delta_y2 - delta_x2 * delta_y1

        # 圆弧半径：
        # 向量积（叉乘）为正值时，表示圆弧逆时针, radius > 0
        # 向量积为负值，表示顺时针, radius < 0,
        if facing < 0:
            radius = -radius

        # 旋转路径到圆弧切线
        if cy != y2:
            adj_yaw = math.atan((x2 - cx) / (cy - y2))
        else:
            if cx > x2:
                adj_yaw = -math.pi / 2
            else:
                adj_yaw = math.pi / 2

        if y2 > cy:
            # 圆弧逆时针
            if radius > 0:
                adj_yaw = math.pi + adj_yaw
        else:
            # 圆弧shun时针
            if radius < 0:
                adj_yaw = math.pi + adj_yaw

        tangent_angle = AngleUtils.normalize_360(math.degrees(adj_yaw))
        if not AngleUtils.equal_norm(cur_angle, tangent_angle, 5):
            paths.append(Path.create_rotate_path(int(adj_yaw * 1000)))

        cur_angle = arc_end['angle']

        paths.append(
            Path.create_circle_path(
                int(x2),
                int(y2),
                int(x1),
                int(y1),
                int(cx),
                int(cy),
                int(radius),
                direction,
                limit_v=limit_v,
            )
        )

        distance = GeometryUtils.calculate_distance(
            arc_end['x'], arc_end['y'], target_pos['x'], target_pos['y']
        )
        if distance > SHORT_PATH_LEN:
            # 旋转路径
            yaw = GeometryUtils.calculate_angle(
                arc_end['x'], arc_end['y'], target_pos['x'], target_pos['y']
            )

            line_angle = AngleUtils.normalize_360(math.degrees(yaw))
            if not AngleUtils.equal_norm(cur_angle, line_angle, 5):
                paths.append(Path.create_rotate_path(int(yaw * 1000)))

            # 圆弧终点和目标点直线路径
            paths.append(
                Path.create_line_path(
                    arc_end['x'],
                    arc_end['y'],
                    target_pos['x'],
                    target_pos['y'],
                    direction,
                    limit_v=limit_v,
                )
            )

        return paths

    # 根据起点切线和切线外圆弧一点计算圆弧
    def calculate_arc_path_by_start_tangent(self, cur_pos):
        # 调度系统发的圆弧路径规则
        # 1、还未到圆弧起点位置即提前发了路径
        # 2、圆弧点参数中有两个点，第一个点为圆弧起点,第二个点为圆弧终点，目标点与第二个点连线为圆弧切线
        # 3、算法：收到圆弧路径时，生成三段路径一起发给小车
        # 当前车的起点和圆弧起点的直线路径(不考虑旋转)
        # 圆弧路径
        # 圆弧终点和目标点的切线直线路径

        path_points = self.path_points
        if len(path_points) <= 1:
            _logger.error('Illegal path points size ' + str(len(path_points)))
            return []

        paths = []

        is_backward = self.is_move_backward()
        if is_backward:
            direction = Direction.BackForward
        else:
            direction = Direction.Forward

        arc_start = {
            'x': path_points[0].x,
            'y': path_points[0].y,
            'angle': path_points[0].angle / 1000,
        }
        arc_end = {
            'x': path_points[-1].x,
            'y': path_points[-1].y,
            'angle': path_points[-1].angle / 1000,
        }

        target_pos = self.get_move_target()

        limit_v = self.get_limit_v()

        distance = GeometryUtils.calculate_distance(
            cur_pos['x'], cur_pos['y'], arc_start['x'], arc_start['y']
        )
        # 路径很短时不要发送短路径，以免报src起始角度偏差过大
        if distance > SHORT_PATH_LEN:
            # 旋转路径
            yaw = GeometryUtils.calculate_angle(
                cur_pos['x'], cur_pos['y'], arc_start['x'], arc_start['y']
            )
            paths.append(Path.create_rotate_path(int(yaw * 1000)))

            # 当前位置和圆弧起点直线路径
            paths.append(
                Path.create_line_path(
                    cur_pos['x'],
                    cur_pos['y'],
                    arc_start['x'],
                    arc_start['y'],
                    direction,
                    limit_v=limit_v,
                )
            )

        # 默认小车移动到圆弧起点位置时朝向是圆弧，不需要添加旋转路径???如果这里也需要旋转则两点无法确定圆弧

        # 计算圆弧路径
        x1 = arc_start['x']
        y1 = arc_start['y']

        x2 = arc_end['x']
        y2 = arc_end['y']
        tangent_slope = math.tan(math.radians(cur_pos['angle'] / 1000))
        a = -(x2 - x1) / (y2 - y1)
        b = (pow(x2, 2) + pow(y2, 2) - pow(x1, 2) - pow(y1, 2)) / (2 * (y2 - y1))
        if tangent_slope != float('inf'):
            cx = (x1 + tangent_slope * y1 - tangent_slope * b) / (a * tangent_slope + 1)
            cy = (x1 + tangent_slope * y1 - cx) / tangent_slope

            radius = math.sqrt(pow(x1 - cx, 2) + pow(y1 - cy, 2))
        else:
            # 圆弧切线垂直x轴
            cy = y1
            cx = (b - y1) / a
            radius = math.fabs(cx - x1)

        delta_x1 = x1 - cx
        delta_y1 = y1 - cy
        delta_x2 = x2 - x1
        delta_y2 = y2 - y1
        facing = delta_x1 * delta_y2 - delta_x2 * delta_y1

        # 圆弧半径：
        # 向量积（叉乘）为正值时，表示圆弧逆时针, radius > 0
        # 向量积为负值，表示顺时针, radius < 0,
        if facing < 0:
            radius = -radius

        paths.append(
            Path.create_circle_path(
                int(x1),
                int(y1),
                int(x2),
                int(y2),
                int(cx),
                int(cy),
                int(radius),
                direction,
                limit_v=limit_v,
            )
        )

        distance = GeometryUtils.calculate_distance(
            arc_end['x'], arc_end['y'], target_pos['x'], target_pos['y']
        )
        if distance > SHORT_PATH_LEN:
            # 旋转路径
            yaw = GeometryUtils.calculate_angle(
                arc_end['x'], arc_end['y'], target_pos['x'], target_pos['y']
            )
            paths.append(Path.create_rotate_path(int(yaw * 1000)))

            # 圆弧终点和目标点直线路径
            paths.append(
                Path.create_line_path(
                    arc_end['x'],
                    arc_end['y'],
                    target_pos['x'],
                    target_pos['y'],
                    direction,
                    limit_v=limit_v,
                )
            )

        return paths

    # 根据三点计算圆弧路径
    def calculate_arc_path_by_points(self, cur_pos):
        if not cur_pos:
            return []

        if not self.is_task_arc_move():
            _logger.error('Calculate arc path when not arc move task')
            return []
        path_points = self.path_points
        if len(path_points) <= 1:
            _logger.error(f'Illegal path points size {len(path_points)}')
            return []

        internal_pos = {'x': path_points[0].x, 'y': path_points[0].y}
        end_pos = {
            'x': path_points[len(path_points) - 1].x,
            'y': path_points[len(path_points) - 1].y,
        }

        # 三点(当前机器人位置、任意一个中间点、终点)确定一个圆弧
        is_backward = self.is_move_backward()
        if is_backward:
            direction = Direction.BackForward
        else:
            direction = Direction.Forward

        paths = []
        cx, cy, radius = GeometryUtils.calculate_circle(cur_pos, internal_pos, end_pos)
        _logger.info(f'calculate_arc_path_by_points(): cx={cx} cy={cy} r={radius}')
        paths.append(
            Path.create_circle_path(
                int(cur_pos['x']),
                int(cur_pos['y']),
                int(end_pos['x']),
                int(end_pos['y']),
                int(cx),
                int(cy),
                int(radius),
                direction,
            )
        )
        return paths

    def _calculate_bezier_ctrl_pos(self, unit_vector, start_pos, pos):
        unit_x = unit_vector['x']
        unit_y = unit_vector['y']

        start_x = start_pos['x']
        start_y = start_pos['y']

        pos_x = pos['x']
        pos_y = pos['y']

        # 以x方向计算
        if abs(unit_x) > abs(unit_y):
            offset_x = (pos_x - start_x) * GOLDEN_SECTION_RATIO
            if abs(offset_x) < BEZIER_CTRL_POS_THRESHOLD:
                if offset_x >= 0:
                    offset_x = BEZIER_CTRL_POS_THRESHOLD
                else:
                    offset_x = -BEZIER_CTRL_POS_THRESHOLD
            if abs(unit_x) <= 0.00001:
                offset_y = 0
            else:
                offset_y = offset_x * unit_y / unit_x
        else:  # 以y方向计算
            offset_y = (pos_y - start_y) * GOLDEN_SECTION_RATIO
            if abs(offset_y) < BEZIER_CTRL_POS_THRESHOLD:
                if offset_y >= 0:
                    offset_y = BEZIER_CTRL_POS_THRESHOLD
                else:
                    offset_y = -BEZIER_CTRL_POS_THRESHOLD
            if abs(unit_y) <= 0.00001:
                offset_x = 0
            else:
                offset_x = offset_y * unit_x / unit_y
        result = int(start_x + offset_x), int(start_y + offset_y)
        return result

    def get_arc_max_speed(self):
        max_speed = self.get_limit_v()
        for p in self.path_points:
            if p.get_max_speed() < max_speed:
                max_speed = p.get_max_speed()
        return max_speed

    def __str__(self):
        result = super().__str__()
        result += '\n  path_points: [{}]'.format(','.join([x.__str__() for x in self.path_points]))
        return result
