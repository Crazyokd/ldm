#!/usr/bin/python3

import math
import time
import logging
import pytest
from typing import List

from test.alarm_server import AlarmServer
from test.robots_control_system import RobotsControlSystem
from protocol_adapter.utils.geometry import GeometryUtils
from protocol_adapter.utils.angle import AngleUtils
from protocol_adapter.models.state import SystemState
from protocol_adapter.huawei_model.point import Point as HuaweiPoint, SimplePoint
from protocol_adapter.huawei_model.utils_plot import (
    create_task_and_plot_path_from_points,
    get_transformed_path_and_target,
)


_logger = logging.getLogger(__name__)


def get_path_start_angle_deg(paths: List[List[SimplePoint]]):
    """计算路径起点方向"""
    for path in paths:
        # 默认直线或者 5 阶贝塞尔
        assert len(path) in (2, 6)
        p0, p1 = path[0], path[1]
        return math.degrees(math.atan2(p1.y - p0.y, p1.x - p0.x))


def get_rotate_anggle_to_90n(paths, cur_pose):
    """将路径旋转到起始方向与当前 90n 方向一致"""
    rotate_angle = 0
    path_start_angle = get_path_start_angle_deg(paths)
    if path_start_angle is not None:
        cur_angle_deg = cur_pose.angle / 1000
        rotate_angle = path_start_angle - AngleUtils.to_90n(cur_angle_deg)

    return rotate_angle


def debug_paths_and_points(
    paths: List[List[SimplePoint]],
    dst_point: HuaweiPoint,
    cur_point: HuaweiPoint,
    move_pose: List[SimplePoint],
    save_to: str = 'task_path.png',
):
    # DEBUG: 打印转换后的座标
    msg_echo = []
    msg_echo.append('transformed paths:')
    for path in paths:
        msg_echo.extend(
            f'  SimplePoint({point.x}, {point.y}, {point.point_type}, {point.limit_v})'
            for point in path
        )
        msg_echo.append('')
    msg_echo.append('transformed position:')
    msg_echo.append(f'  dst pose: Point{dst_point}')
    msg_echo.append(f'  cur pose: Point{cur_point}')
    print('\n'.join(msg_echo))

    # DEBUG: 如果需要检查绘制路径
    create_task_and_plot_path_from_points(
        paths,
        dst_point,
        cur_point,
        move_pose,
        save_to=save_to,
    )


@pytest.mark.env('real_car')
class TestWithRealCar:
    """
    用于 ldm 仿真 + 真车测试:

    0. 切工作目录
    1. 初始化虚拟环境: make && make build
    2. 配置小车: 启用 ldm 模块，配置仿真地址和端口 8988
    3. 运行仿真测试用例(自动启用 ldm 服务端仿真，并按用例给小车发任务):
        uv run pytest -vs -E real_car test/real_car_test.py

    主要用于真车问题复现配合手动调试，按需自定义用例
    """

    rcs: RobotsControlSystem

    @pytest.fixture(scope='function', autouse=True)
    def up_and_down(self):
        # 启动服务端
        alarm_server = AlarmServer()
        self.rcs = RobotsControlSystem()
        self.rcs.start()

        # 等待小车注册
        self.rcs.wait_client_register()

        # 执行测试用例
        yield

        # 停止服务端
        self.rcs.stop()
        alarm_server.stop()

    def waiting_system_state(self, state, time_out_s: float = 60) -> bool:
        CHECK_INTERVAL_HZ = 10
        for i in range(int(time_out_s * CHECK_INTERVAL_HZ)):
            time.sleep(1 / CHECK_INTERVAL_HZ)
            curr_state = self.rcs.system_state
            if i % CHECK_INTERVAL_HZ == 0:
                _logger.debug(
                    f'Waiting car {state} {i // CHECK_INTERVAL_HZ}s, cur state: {curr_state},'
                    f' {self.rcs.get_cur_point()}'
                )
            if curr_state.value == state.value:
                return True
        return False

    def test_move_on_suspicious_bezier_path(self):
        """车在可疑贝塞尔末端的异常：
        1. 末端附近转圈
        2. 末端提前停止
        """

        # 等待小车空闲后，拿当前位置
        self.waiting_system_state(SystemState.IDLE)
        real_cur_point = self.rcs.get_cur_point()  # mm, mdeg

        # 路径组座标点 (X_mm, Y_mm, path_type, path_limit_v)
        paths = [
            [
                SimplePoint(110295, 104175, 1, 500),
                SimplePoint(110295, 103998, 1, 500),
                SimplePoint(110295, 103821, 1, 500),
                SimplePoint(111028, 103821, 1, 500),
                SimplePoint(111394, 103821, 1, 500),
                SimplePoint(111760, 103821, 1, 500),
            ]
        ]

        # 当前小车位资，目标点位姿 (X_mm, Y_mm, Yaw_mdeg)
        cur_point = HuaweiPoint(110293, 104175, -89954)
        dst_point = HuaweiPoint(111760, 103821, 0)

        # 移动轨迹点(SimplePoint)，用于调试绘图
        move_pose = []

        # 变换座标
        rotate_angle = get_rotate_anggle_to_90n(paths, real_cur_point)
        paths, dst_point, cur_point = get_transformed_path_and_target(
            paths,
            dst_point,
            cur_point,
            rotate_deg=rotate_angle,
            scale=1,
            ref_point=paths[0][0],
            ref_point_after=real_cur_point,  # 将起点设为当前点（转换后的当前点）
        )

        # 打印转换后的调试信息
        debug_paths_and_points(paths, cur_point=cur_point, dst_point=dst_point, move_pose=move_pose)

        # 每个任务完成后需要变更任务 id
        task_id = 0

        # 给小车周期性发送移动任务
        while True:
            self.rcs.move_multi_paths_with_no_payload(
                dst_point,
                points_groups=paths,
                task_id=task_id,
                sub_task_id=255,
            )

            # 模拟 1s 周期重发任务
            time.sleep(1)

            # 到达目标空闲后 任务 id+1，退出
            if (
                GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point())
                and self.rcs.system_state.value == SystemState.IDLE.value
            ):
                task_id += 1
                break

        # 自定义真车测试逻辑
