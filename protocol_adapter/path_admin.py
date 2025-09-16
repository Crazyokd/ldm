import logging
import math
from typing import Optional

from protocol_adapter.protobuf_wrapper.path import Direction, Path, PathType

_logger = logging.getLogger(__name__)


# 路径管理，为了使小车移动看起来流畅，需要支持路径替换功能
# 进行路径替换时，需要将所有路径都下发给sros，例如:
# 当前收到直线任务，发给小车，小车在移动过程中接收到圆弧路径任务，则需要将直线路径和圆弧路径再次发给小车
class PathAdmin:
    def __init__(self):
        # 记录计算路径时起始点坐标和方向, 单位mm 1/1000度
        self._path_start_pose = None

        # 数据格式: 每个任务生成一个路径组，
        # 替换路径时，替换指定路径组
        # [
        #   [path1, path2, path3],
        #   [path1, path2, path3],
        #   [path1, path2, path3]
        # ]
        self._paths = []

    def set_path_start_pose(self, pose):
        self._path_start_pose = pose

    # 追加路径组
    def append(self, paths):
        # 必须等待旋转路径组执行完成
        if self.has_rotate_path_group():
            _logger.warning('fail to append path, wait rotate path done')
            return False
        self._paths.append(paths)
        return True

    # 替换最后一段路径
    def replace(self, paths):
        # 必须等待旋转路径组执行完成
        if self.has_rotate_path_group():
            _logger.warning('fail to replace path, wait rotate path done')
            return False

        if len(self._paths) > 0:
            self._paths[-1] = paths
        else:
            self._paths.append(paths)
            _logger.warning('append path group while on replace path group')
        return True

    def get_lastest_path_end_pose(self, path_groups):
        """获取最后一个路径终点的位姿"""
        pose_angle = None
        for path_group in reversed(path_groups):
            for path in reversed(path_group):
                if pose_angle is None:
                    pose_angle = round(path.end_facing() * 1000)
                if path.type in (PathType.PATH_LINE, PathType.PATH_BEZIER):
                    return {'x': path.ex, 'y': path.ey, 'angle': pose_angle}
        return {'x': 0, 'y': 0, 'angle': 0 if pose_angle is None else pose_angle}

    # 获取替换路径的起始点
    # is_append: 替换路径时是否以追加方式替换
    # 1、直线路径替换直线路径，圆弧路径替换圆弧路径且弧线点相同，此时应该将原来路径组替换，
    # 使用原路径组的第一条路径起点作为替换路径起点
    # 2 如果直线路径->圆弧路径和圆弧路径->直线路径方式的替换，
    #   最后一段路径的坐标和方向作为替换路径起点, 新路径组以追加方式替换原路径组
    def get_replace_path_start_pose(self, is_append):
        if len(self._paths) <= 0:
            return None

        path_group = self._paths[-1]
        if len(path_group) <= 0:
            return None

        # 追加路径，追加路径角度和坐标点直接使用上一个路径组的坐标和角度，可以保证连续
        if is_append:
            return self.get_lastest_path_end_pose(self._paths)

        # 替换路径，选择倒数第二路径组最后一条路径目标点作为替换路径点，
        # 如果路径组不超过1，则使用记录的点
        if len(self._paths) < 2:
            return self._path_start_pose

        path_group = self._paths[-2]
        if len(path_group) <= 0:
            return None

        return self.get_lastest_path_end_pose(self._paths[:-1])

    # 返回最后一组路径的指定类型路径
    def get_latest_path_by_type(self, path_type):
        if len(self._paths) <= 0:
            return None
        for path in reversed(self._paths[-1]):
            if path.type == path_type:
                return path
        return None

    def filter_paths(self, paths):
        """路径过滤优化

        目前处理的情况包括：
        1. 替换已发送的直线路径，更新已有限速：由于路径替换都是作为新路径组追加，既有路径不会修改；
            然而更新已有限速需要更新既有路径，所以放在最终发送路径前处理；更新限速路径时，会将路径的
            起点设为被替换路径的起点，在这里看到连续直线路径，起点相同，才进行合并处理；
        2. 连续旋转路径，简化成最后一个旋转
        """

        last_path = None
        filtered_paths = []

        for path in paths:
            ref_path = last_path
            last_path = path

            # 检查处理可以合并的直线路径:
            # 1. 连续相同起点的直线，无条件用后面的直线替换
            # 2. 连续旋转路径，直接使用后面的旋转替换
            if (
                ref_path
                and ref_path.type == path.type
                and (
                    ref_path.type == PathType.PATH_ROTATE
                    or (
                        ref_path.type == PathType.PATH_LINE
                        and path.sx == ref_path.sx
                        and path.sy == ref_path.sy
                    )
                )
            ):
                filtered_paths[-1] = path
                continue

            filtered_paths.append(path)

        return filtered_paths

    def get_all(self, *, apply_filter: bool = True):
        paths = [path for path_group in self._paths for path in path_group]
        return self.filter_paths(paths) if apply_filter else paths

    def get_last_path(self) -> Optional[Path]:
        return self._paths[-1][-1] if self._paths and self._paths[-1] else None

    def has_pending_path(self):
        return len(self._paths) > 0

    def clear(self):
        self._paths = []

    # 是否存在旋转路径组，如果存在旋转路径组(可能包含直线路径，先直线后旋转)，需等待执行完成(因为旋转需要申请空间)
    def has_rotate_path_group(self):
        return any(self.is_rotate_path_group(path_group) for path_group in self._paths)

    # 是否是旋转路径组
    def is_rotate_path_group(self, path_group):
        result = False
        for i, path in enumerate(path_group):
            if path.type == PathType.PATH_LINE:
                continue
            # 贝塞尔路径组允许存在旋转路径（不申请旋转空间）
            elif path.type == PathType.PATH_BEZIER:
                return False
            elif path.type == PathType.PATH_ROTATE:
                if path.direction == Direction.SHELF_LEG_IDENTIFY:  # 货架识别不算旋转
                    continue
                if len(path_group) > i + 1:  # 接着贝塞尔的旋转不需要申请空间
                    if path_group[i + 1].type == PathType.PATH_BEZIER:
                        return False
                return True
        return result

    def self_has_not_forward_path(self):
        return any(self.has_not_forward_path(path_group) for path_group in self._paths)

    def has_not_forward_path(self, path_group):
        return any(path.direction != Direction.Forward for _, path in enumerate(path_group))

    def replace_path_if_in_one_line(self, x, y):
        for i, path_group in enumerate(self._paths):
            for j, path in enumerate(path_group):
                if path.type == PathType.PATH_LINE and path.is_inner_point(x, y):
                    self._paths = self._paths[: i + 1]
                    self._paths[i] = self._paths[i][: j + 1]
                    self._paths[i][j].ex = x
                    self._paths[i][j].ey = y
                    return True
        return False

    def __str__(self) -> str:
        lines = [
            f'Path group length: {len(self._paths)}',
        ]
        for idx, path_group in enumerate(self._paths):
            lines.append(f'# path group {idx}')
            for j, path in enumerate(path_group):
                lines.append(f'{j}th: {path}')
        return '\n  '.join(lines)
