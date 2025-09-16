import logging
import math
import numpy as np
from typing import List

from protocol_adapter.models.task import TaskType
from protocol_adapter.huawei_model.point import Point, SimplePoint
from protocol_adapter.huawei_model.move_target import MoveTarget
from protocol_adapter.huawei_model.multi_move_task import MultiMoveTask
from protocol_adapter.protobuf_wrapper.path import PathType, Path
from protocol_adapter.huawei_model.bezier import (
    CubicBezier,
    QuinticBezier,
)


# 设置 matplotlib 模块的日志级别
logging.getLogger('matplotlib').setLevel(logging.WARNING)


# 将 Path 列表转换为 3 阶贝塞尔曲线
def path_to_cubic_bezier(path: Path):
    return CubicBezier(
        [path.sx / 1000.0, path.sy / 1000.0],
        [path.cx / 1000.0, path.cy / 1000.0],
        [path.dx / 1000.0, path.dy / 1000.0],
        [path.ex / 1000.0, path.ey / 1000.0],
    )


# 函数：将 SimplePoint 列表转换为 5 阶贝塞尔曲线
def simple_points_to_quintic_bezier(points: list):
    if len(points) != 6:
        raise ValueError('必须提供 6 个 SimplePoint 控制点')

    # 从 SimplePoint 中提取坐标
    p0 = [points[0].x / 1000.0, points[0].y / 1000.0]
    p1 = [points[1].x / 1000.0, points[1].y / 1000.0]
    p2 = [points[2].x / 1000.0, points[2].y / 1000.0]
    p3 = [points[3].x / 1000.0, points[3].y / 1000.0]
    p4 = [points[4].x / 1000.0, points[4].y / 1000.0]
    p5 = [points[5].x / 1000.0, points[5].y / 1000.0]

    # 返回 QuinticBezier 对象
    return QuinticBezier(p0, p1, p2, p3, p4, p5)


def task_plot(task: MultiMoveTask, curr_pose, move_pose=None, save_to=None):
    """绘制任务的贝塞尔，当前车位置和拟合出来的贝塞尔"""
    import matplotlib.pyplot as plt

    def plot_quintic_bezier(bezier: QuinticBezier):
        t_values = np.linspace(0, 1, 1000)
        curve_points = np.array([bezier.curve(t) for t in t_values])

        # 绘制贝塞尔曲线，并设置标签
        plt.plot(curve_points[:, 0], curve_points[:, 1], color='#00FF00', label='ldm 5b')

        # 绘制控制点
        plt.scatter(
            [bezier.p0[0], bezier.p1[0], bezier.p2[0], bezier.p3[0], bezier.p4[0], bezier.p5[0]],
            [bezier.p0[1], bezier.p1[1], bezier.p2[1], bezier.p3[1], bezier.p4[1], bezier.p5[1]],
            color='yellow',
            label='Control Points',
        )

        # 绘制控制点之间的连线
        control_points = np.array(
            [bezier.p0, bezier.p1, bezier.p2, bezier.p3, bezier.p4, bezier.p5]
        )
        plt.plot(
            control_points[:, 0],
            control_points[:, 1],
            '--',
            color='yellow',
            label='Control Point Lines',
        )

    def plot_cubic_bezier(bezier: CubicBezier):
        t_values = np.linspace(0, 1, 1000)
        curve_points = np.array([bezier.curve(t) for t in t_values])

        plt.plot(curve_points[:, 0], curve_points[:, 1], color='blue', label='std b3')
        plt.scatter(
            [bezier.p0[0], bezier.p1[0], bezier.p2[0], bezier.p3[0]],
            [bezier.p0[1], bezier.p1[1], bezier.p2[1], bezier.p3[1]],
            color='red',
            label='Control Points',
        )
        # 绘制控制点之间的连线
        control_points = np.array([bezier.p0, bezier.p1, bezier.p2, bezier.p3])
        plt.plot(control_points[:, 0], control_points[:, 1], 'r--', label='b3 control point lines')

    # 设置图形
    plt.figure(figsize=(12, 6))
    plt.axis('equal')  # 设置坐标轴等比例

    # 遍历路径点并绘制贝塞尔曲线
    for path_points in task.path_points_groups:
        if path_points[0].point_type == 0:  # 直线路径
            plt.plot(
                [path_points[0].x / 1000.0, path_points[-1].x / 1000.0],
                [path_points[0].y / 1000.0, path_points[-1].y / 1000.0],
                color='#00F000',
                label='ldm line',
            )
        elif path_points[0].point_type == 1:
            b5 = simple_points_to_quintic_bezier(path_points)
            plot_quintic_bezier(b5)

    plt.scatter(
        curr_pose['x'] / 1000.0,
        curr_pose['y'] / 1000.0,
        color='blue',
        label='Start Point',
        zorder=5,
    )
    # 绘制当前车辆朝向（yaw）箭头
    yaw_rad = np.deg2rad(curr_pose['angle'] / 1000.0)
    arrow_length = 0.02  # 设置箭头的长度

    plt.arrow(
        curr_pose['x'] / 1000.0,
        curr_pose['y'] / 1000.0,  # 起始位置
        arrow_length * np.cos(yaw_rad),  # 箭头在 x 轴的分量
        arrow_length * np.sin(yaw_rad),  # 箭头在 y 轴的分量
        head_width=0.02,  # 箭头头部的宽度
        head_length=0.02,  # 箭头头部的长度
        fc='blue',  # 箭头的颜色
        ec='blue',  # 箭头边框的颜色
        label='vehicle facing',
    )

    paths = task.calculate_move_path(curr_pose, need_check_start_pose=True)
    for i, path in enumerate(paths):
        print(f'{i}th: {path}')
        if path.type == PathType.PATH_LINE:
            plt.plot(
                [path.sx / 1000.0, path.ex / 1000.0],
                [path.sy / 1000.0, path.ey / 1000.0],
                color='blue',
                label='std line',
            )
        elif path.type == PathType.PATH_BEZIER:
            b3 = path_to_cubic_bezier(path)
            plot_cubic_bezier(b3)

    if move_pose:
        x = [pose.x / 1000 for pose in move_pose]
        y = [pose.y / 1000 for pose in move_pose]
        plt.plot(x, y, color='#ffcc22', marker='o', linestyle=':', label='move pose')

    # 手动添加特殊点
    # plt.scatter(110.730, 103.758, marker='x', color='red', label='crash')

    # 添加图例
    plt.legend(loc='best')

    # 设置标题和轴标签
    plt.title('ldm task to standard-robots task')
    plt.xlabel('x')
    plt.ylabel('y')

    plt.tight_layout()

    # 显示图形，或者保存成图片(如果容器里不好显示的话)
    if save_to:
        plt.savefig(save_to)
    else:
        plt.show()  # xhost +


def transform_by_rotate_scale_and_move(
    points: List[SimplePoint],
    rotate_deg: float,
    scale: float,
    ref_point: SimplePoint,
    ref_point_after: SimplePoint,
) -> List[SimplePoint]:
    # 转换成弧度
    rotate_angle = math.radians(rotate_deg)

    # 构建平移矩阵
    translation_matrix = np.array(
        [
            [1, 0, ref_point_after.x - ref_point.x],
            [0, 1, ref_point_after.y - ref_point.y],
            [0, 0, 1],
        ]
    )

    # 构建旋转矩阵
    rotation_matrix = np.array(
        [
            [np.cos(rotate_angle), -np.sin(rotate_angle), 0],
            [np.sin(rotate_angle), np.cos(rotate_angle), 0],
            [0, 0, 1],
        ]
    )

    # 构建缩放矩阵
    scale_matrix = np.array(
        [
            [scale, 0, 0],
            [0, scale, 0],
            [0, 0, 1],
        ]
    )

    # 构建仿射变换矩阵
    affine_matrix = np.dot(rotation_matrix, np.dot(scale_matrix, translation_matrix))

    # 对每个点进行变换
    transformed_points = []
    for point in points:
        # 将点转换为齐次坐标
        point_homogeneous = np.array([point.x, point.y, 1])

        # 应用仿射变换
        transformed_point_homogeneous = np.dot(affine_matrix, point_homogeneous)

        # 将齐次坐标转换回普通坐标
        transformed_point = (transformed_point_homogeneous[0], transformed_point_homogeneous[1])

        # 创建新的SimplePoint对象并添加到结果列表中
        transformed_points.append(
            SimplePoint(transformed_point[0], transformed_point[1], point.point_type, point.limit_v)
        )

    return transformed_points


def get_transformed_path_and_target(
    paths: List[List[SimplePoint]],
    dst_point: Point,
    cur_point: Point,
    rotate_deg: float,
    scale: float,
    ref_point: SimplePoint,
    ref_point_after=None,
):
    if ref_point_after is None:
        ref_point_after = SimplePoint()

    paths = paths.copy()
    paths.append(
        [
            SimplePoint(dst_point.x, dst_point.y),
            SimplePoint(cur_point.x, cur_point.y),
        ]
    )

    def convert_path(path):
        path_cvt = transform_by_rotate_scale_and_move(
            path,
            rotate_deg=rotate_deg,
            scale=scale,
            ref_point=ref_point,
            ref_point_after=ref_point_after,
        )

        # 强制转整型(都是 mm 单位，应该够了)，以便后面 task 直接用
        for point in path_cvt:
            point.x = int(point.x)
            point.y = int(point.y)

        return path_cvt

    new_paths = [convert_path(path) for path in paths]

    points = new_paths.pop()
    dst_point = Point(points[0].x, points[0].y, dst_point.angle + int(rotate_deg * 1000))
    cur_point = Point(points[1].x, points[1].y, cur_point.angle + int(rotate_deg * 1000))

    return (new_paths, dst_point, cur_point)


def create_task_and_plot_path_from_points(
    paths: List[List[SimplePoint]],
    dst_point: Point,
    cur_point: Point,
    move_pose: List[SimplePoint],
    save_to=None,
):
    task = MultiMoveTask(TaskType.Multi_Path_No_Payload_Move)
    task.path_points_groups = paths
    task.move_target = MoveTarget()
    task.move_target.x = dst_point.x
    task.move_target.y = dst_point.y
    task.move_target.angle = dst_point.angle

    curr_pose = {'x': cur_point.x, 'y': cur_point.y, 'angle': cur_point.angle}
    task_plot(task, curr_pose, move_pose=move_pose, save_to=save_to)
