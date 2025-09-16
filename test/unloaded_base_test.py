#!/usr/bin/python3
# Copyright 2024 Standard Robots Co. All rights reserved.
import time
import unittest
import logging

from protocol_adapter.utils import GeometryUtils
from protocol_adapter.models.state import SystemState
from protocol_adapter.huawei_model.point import Point as HuaweiPoint, SimplePoint
from protocol_adapter.huawei_model.utils_plot import (
    create_task_and_plot_path_from_points,
)
from protocol_adapter.mock.world_mock import WorldMock
from protocol_adapter.protobuf_wrapper.base import Pose
from protocol_adapter.adapter_admin import AdapterAdmin

from test.alarm_server import AlarmServer
from test.robots_control_system import RobotsControlSystem

_logger = logging.getLogger(__name__)


class UnloadedBaseTest(unittest.TestCase):
    """没负载的基础测试，多车型都可以使用"""

    def setUp(self):
        self.alarm_server = AlarmServer()
        self.rcs = RobotsControlSystem()
        self.rcs.start()
        self.adapter_admin = AdapterAdmin(mock=True)
        self.adapter_admin.run()
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

    def tearDown(self):
        self.rcs.stop()
        self.alarm_server.stop()
        self.adapter_admin.stop()
        WorldMock().reset()
        time.sleep(0.2)  # 等待端口关闭

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

    def waiting_something(self, code_to_exec: str, time_out_s=60) -> bool:
        CHECK_INTERVAL_HZ = 10
        for i in range(int(time_out_s * CHECK_INTERVAL_HZ)):
            time.sleep(1 / CHECK_INTERVAL_HZ)
            curr_state = self.rcs.system_state
            if i % CHECK_INTERVAL_HZ == 0:
                _logger.debug(
                    f'Waiting {{{code_to_exec}}} {i // CHECK_INTERVAL_HZ}s, cur state: {curr_state},'
                    f' {self.rcs.get_cur_point()}'
                )
            if eval(code_to_exec):
                return True
        return False

    def test_move_forward(self):
        """测试车辆空车往前移动"""
        point = self.rcs.get_cur_point()
        point.x += 2000
        self.rcs.move_to_pose(point)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertTrue(GeometryUtils.is_same_point(point, self.rcs.get_cur_point()))

    def test_angle_rotate_only(self):
        "测试下位置点不变，只旋转角度"
        point = self.rcs.get_cur_point()
        point.angle = 180000
        self.rcs.move_to_pose(point)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertTrue(GeometryUtils.is_same_point(point, self.rcs.get_cur_point()))

    def test_move_multi_path(self):
        "测试多路径导航情况"
        self.adapter_admin.set_sros_pose(Pose(118.329, 141.391, -0.057))
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置
        dst_point = HuaweiPoint(121462, 140229, -90000)
        self.rcs.move_multi_paths_with_no_payload(
            dst_point,
            points_groups=[
                [SimplePoint(114054, 141390, 0), SimplePoint(120119, 141390, 0)],
                [
                    SimplePoint(120119, 141390, 1),
                    SimplePoint(120455, 141390, 1),
                    SimplePoint(120791, 141390, 1),
                    SimplePoint(121462, 141390, 1),
                    SimplePoint(121462, 140810, 1),
                    SimplePoint(121462, 140229, 1),
                ],
            ],
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        cur_pose = self.rcs.get_cur_point()
        self.assertAlmostEqual(dst_point.x, cur_pose.x, delta=100)
        self.assertAlmostEqual(dst_point.y, cur_pose.y, delta=100)
        self.assertAlmostEqual(dst_point.angle, cur_pose.angle, delta=1000)

    def test_movetask_state_finish_and_idle(self):
        """测试移动任务结束后先报任务完成再报空闲
        关联问题：小车移动任务到达目标点后，ldm未判定完成，增加报完成逻辑辅助判断
        """

        self.rcs.move_to_pose(HuaweiPoint(4000, 0, 0))
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.TASK_FINISH))
        point1 = self.rcs.get_cur_point()
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        point2 = self.rcs.get_cur_point()

        # 报任务完成和IDLE的位置应该不变
        self.assertTrue(GeometryUtils.is_same_point(point1, point2))

    def test_charging_and_stop_charging(self):
        """测试充电任务和停止充电任务,充电不允许旋转，车辆距离充电桩1米时，向后退1米插入充电桩充电"""
        world = WorldMock()
        charging_station_pose = Pose(-1, 0, 0)
        world.set_charging_station_pose(charging_station_pose)
        point = self.rcs.get_cur_point()
        point.y = 0
        point.x = -1000
        self.rcs.charge(point)
        self.assertTrue(self.waiting_system_state(SystemState.CHARGING))
        self.assertTrue(GeometryUtils.is_same_point(point, self.rcs.get_cur_point()))

        time.sleep(3)

        # 停止充电
        point = self.rcs.get_cur_point()
        self.rcs.stop_charge(point)
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

    def test_move_and_stop_on_move(self):
        """测试移动任务中下发停止操作，预期停止移动
        关联问题：ldm下发停止指令后，触发上传状态过程的异常，小车离线
        """

        # 下发长距离移动任务，一时半会停不下的那种
        self.rcs.move_to_pose(HuaweiPoint(40000, 0, 0))
        self.assertFalse(self.waiting_system_state(SystemState.NONE, time_out_s=1))

        # 模拟下发停止移动，并等待下车停止移到恢复空闲状态
        self.rcs.stop_move()
        self.assertTrue(self.waiting_system_state(SystemState.IDLE, time_out_s=4))

        # 停止移动后获取当前座标，1s 后再次获取，座标不应变动
        point1 = self.rcs.get_cur_point()
        self.assertFalse(self.waiting_system_state(SystemState.NONE, time_out_s=1))
        point2 = self.rcs.get_cur_point()
        self.assertTrue(GeometryUtils.is_same_point(point1, point2))

        # 另外验证关联问题的现象: 设备应当是在线状态
        self.assertTrue(self.waiting_system_state(SystemState.IDLE, time_out_s=1))

    def test_ignore_move_on_off_path(self):
        """测试离下发路径超过 22cm 后，发移动任务，小车应当报偏离路径"""
        self.adapter_admin.set_sros_pose(Pose(0.23, 0, 0))
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        # 到路径起点 21cm, 但在路径上，到路径距离 0，正常走
        dst_point1 = HuaweiPoint(1000, 0, 0)
        self.rcs.move_multi_paths_with_no_payload(
            dst_point1,
            points_groups=[
                [SimplePoint(0, 0, 0), SimplePoint(1000, 0, 0)],
            ],
            task_id=0,
            sub_task_id=255,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.assertTrue(GeometryUtils.is_same_point(dst_point1, self.rcs.get_cur_point()))

        # 到路径起点 21cm, 到路径距离 21cm，不走
        dst_point2 = HuaweiPoint(2000, 0, 0)
        self.rcs.move_multi_paths_with_no_payload(
            dst_point2,
            points_groups=[
                # TODO: zz: 注意，这里 y=0 时测试会失败，需要检查计算路径距离的逻辑
                [SimplePoint(1230, 1, 0), SimplePoint(2000, 0, 0)],
            ],
            task_id=0,
            sub_task_id=255,
        )
        self.waiting_system_state(SystemState.BUSY, time_out_s=0.5)
        # 报偏离路径，不动
        self.assertTrue(self.waiting_system_state(SystemState.NAV_OFF_PATH))
        self.assertTrue(GeometryUtils.is_same_point(dst_point1, self.rcs.get_cur_point()))

        # 再等等，应该还是停在那里
        self.waiting_system_state(SystemState.BUSY, time_out_s=1)
        self.assertTrue(self.waiting_system_state(SystemState.NAV_OFF_PATH))
        self.assertTrue(GeometryUtils.is_same_point(dst_point1, self.rcs.get_cur_point()))

    def test_rotate_path_result_in_off_path(self):
        """移动路径替换导致异常偏航

        1. 多路径移动，弧线接直线
        2. 第一段仅弧线，接近弧线末尾时发后续直线
        3. 重新进入任务检测流程，导致起点计算为 0， 触发异常偏航
        """
        init_pose = Pose(48.069, 199.709, -91.157)
        self.adapter_admin.set_sros_pose(init_pose)
        time.sleep(0.3)  # 等待适配器和调度都更新车的位置

        # 路径组座标点 (X_mm, Y_mm, path_type, path_limit_v)
        paths = [
            [
                SimplePoint(50494, 201870, 1, 300),
                SimplePoint(49887, 201870, 1, 300),
                SimplePoint(49280, 201870, 1, 300),
                SimplePoint(48066, 201870, 1, 300),
                SimplePoint(48066, 200572, 1, 300),
                SimplePoint(48066, 199274, 1, 300),
            ],
        ]

        # 目标点位姿 (X_mm, Y_mm, Yaw_mdeg)
        dst_point = HuaweiPoint(48066, 199274, -90000)

        self.rcs.move_multi_paths_with_no_payload(
            dst_point,
            paths,
            task_id=1,
            sub_task_id=2,
        )

        assert self.waiting_system_state(SystemState.BUSY)
        time.sleep(0.6)

        paths_2 = paths + [
            [
                SimplePoint(48066, 199274, 0, 300),
                SimplePoint(48066, 194468, 0, 300),
            ],
        ]
        dst_point_2 = HuaweiPoint(48066, 194468, -90000)

        self.rcs.move_multi_paths_with_no_payload(
            dst_point_2,
            paths_2,
            task_id=1,
            sub_task_id=2,
        )
        assert self.waiting_system_state(SystemState.BUSY)
        assert self.waiting_system_state(SystemState.IDLE)

        assert GeometryUtils.is_same_point(dst_point_2, self.rcs.get_cur_point())

    def test_re_routing_on_curve(self):
        """测试车辆曲线上重新规划路径
        如：
        车在T字形的左边，第一个任务目标点是T字形的下边，
        然后机器人在走第一个任务过程中，调度下发了暂停和继续，
        再然后调度下发新任务让车到T字形的右边，
        此时需要机器人能正常替换路径到T字形的右边"""
        self.adapter_admin.set_sros_pose(Pose(97.341, 141.395, 0.286))
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置
        dst_point1 = HuaweiPoint(102985, 139043, -90000)
        self.rcs.move_multi_paths_with_no_payload(
            dst_point1,
            points_groups=[
                [SimplePoint(96082, 141390, 0), SimplePoint(101840, 141390, 0)],
                [
                    SimplePoint(101840, 141390, 1),
                    SimplePoint(102126, 141390, 1),
                    SimplePoint(102413, 141390, 1),
                    SimplePoint(102985, 141390, 1),
                    SimplePoint(102985, 140217, 1),
                    SimplePoint(102985, 139043, 1),
                ],
            ],
            task_id=0,
            sub_task_id=255,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))

        self.rcs.pause_task()
        self.assertTrue(self.waiting_system_state(SystemState.PAUSE))
        self.rcs.continue_task()
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))

        # 在曲线上替换路径，等待取消当前正在执行的任务
        dst_point2 = HuaweiPoint(103785, 141390, 0)
        self.rcs.move_to_pose(
            dst_point2,
            task_id=0,
            sub_task_id=255,
        )
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        # 再次重发上一次的任务
        self.rcs.move_to_pose(
            dst_point2,
            task_id=0,
            sub_task_id=255,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.assertTrue(
            GeometryUtils.is_same_point(dst_point2, self.rcs.get_cur_point()), '没有完成路径替换'
        )

    def test_linear_move_task_replace_path(self):
        """测试线性任务，替换路径"""
        self.rcs.move_to_pose(HuaweiPoint(4000, 0, 0))
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        # 注意此处，若时间等待时间过短就会无法完成替换
        self.assertFalse(self.waiting_system_state(SystemState.IDLE, 2.5))
        self.rcs.move_to_pose(HuaweiPoint(8000, 0, 0))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertTrue(
            GeometryUtils.is_same_point(HuaweiPoint(8000, 0, 0), self.rcs.get_cur_point()),
            '路径替换失败，没有到达最终目标点',
        )

    def test_replace_path_with_task_type_change(self):
        """测试路径替换，同一个任务ID，路径类型变更也需要正常无缝替换"""
        self.adapter_admin.set_sros_pose(Pose(80.012, 151.419, 180))
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置
        self.rcs.move_to_pose(
            HuaweiPoint(73030, 151420, 180000),
            task_id=8631,
            sub_task_id=2,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))

        # 注意此处，若时间等待时间过短就会无法完成替换
        self.assertFalse(self.waiting_system_state(SystemState.IDLE, 2.5))
        dst_point = HuaweiPoint(71132, 148632, -90000)
        self.rcs.move_multi_paths_with_no_payload(
            dst_point,
            points_groups=[
                [SimplePoint(77225, 151420, 0), SimplePoint(73030, 151420, 0)],
                [
                    SimplePoint(73030, 151420, 1),
                    SimplePoint(72556, 151420, 1),
                    SimplePoint(72081, 151420, 1),
                    SimplePoint(71132, 151420, 1),
                    SimplePoint(71132, 150027, 1),
                    SimplePoint(71132, 148633, 1),
                ],
                [SimplePoint(71132, 148633, 0), SimplePoint(71132, 148632, 0)],
            ],
            task_id=8631,
            sub_task_id=2,
        )
        self.assertFalse(
            self.waiting_system_state(SystemState.IDLE, 2),
            f'任务中断了一下，没有完成无缝替换？{self.rcs.system_state}',
        )
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.assertTrue(
            GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point()),
            '路径替换失败，没有到达最终目标点',
        )

    def test_switch_task_on_move(self):
        """移动中切换移动任务"""

        dst1_point = HuaweiPoint(2000, 0, 0)
        # 第一个移动任务
        self.rcs.move_to_pose(dst1_point, task_id=0, sub_task_id=255)

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        time.sleep(0.5)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))

        cur_point = self.rcs.get_cur_point()
        self.assertTrue(cur_point.x > 0)

        dst2_point = HuaweiPoint(-2000, 0, 0)
        # 模拟重发任务id变化的任务
        self.rcs.move_to_pose(dst2_point, task_id=1234, sub_task_id=0)

        # 切任务过程保持 BUSY 状态，这里等待 1s，模拟任务发送周期
        self.assertFalse(
            self.waiting_system_state(SystemState.IDLE, 1),
            '切任务过程，在收到下一个周期任务前，短时间内应当保持 BUSY 状态',
        )

        # 模拟周期重发任务id变化的任务
        self.rcs.move_to_pose(dst2_point, task_id=1234, sub_task_id=0)

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.assertTrue(GeometryUtils.is_same_point(dst2_point, self.rcs.get_cur_point()))

    def test_change_map(self):
        point = HuaweiPoint(-462, 4278, -89000)
        dmcode_type = 'BB'
        self.rcs.change_map(dmcode_type, '127.0.0.1', self.rcs.get_server_port(), point)
        self.assertTrue(
            self.waiting_something(f'self.rcs.dmcode_type == "{dmcode_type}"'), '切换地图失败'
        )

    def test_pause_continue_stop_restart_move(self):
        """暂停继续任务时，ldm有概率在下发继续后，立马取消任务，并又重启此次任务"""
        point = HuaweiPoint(4000, 0, 0)
        self.rcs.move_to_pose(point)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertFalse(self.waiting_system_state(SystemState.IDLE, time_out_s=0.2))

        self.rcs.pause_task()
        self.assertTrue(self.waiting_system_state(SystemState.PAUSE))
        self.rcs.continue_task()
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertFalse(self.waiting_system_state(SystemState.IDLE, time_out_s=0.3))
        self.rcs.stop_move()
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.rcs.move_to_pose(point)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertTrue(GeometryUtils.is_same_point(point, self.rcs.get_cur_point()))

    def test_pause_on_move_done_and_continue(self):
        """
        测试移动结束后空闲，发暂停然后继续，系统状态应该正常切换
        """
        point = HuaweiPoint(2000, 0, 0)
        self.rcs.move_to_pose(point)

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.rcs.pause_task()
        self.assertTrue(self.waiting_system_state(SystemState.PAUSE))

        self.rcs.continue_task()
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

    def test_pause_on_reboot_and_continue(self):
        """
        测试重启后，空闲收到暂停然后继续，系统状态应该正常切换

        关联问题：
            系统初始启动未曾收到任务时，收到暂停，后面再继续无法恢复
        """
        self.rcs.pause_task()
        self.assertTrue(self.waiting_system_state(SystemState.PAUSE))

        self.rcs.continue_task()
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

    def test_sim_ldm_modify_map(self):
        """模拟ldm改图，改图后会先暂停车，然后ldm掉线，然后发继续，最后发之前相同的任务"""
        point = HuaweiPoint(4000, 0, 0)
        self.rcs.move_to_pose(point)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertFalse(self.waiting_system_state(SystemState.IDLE, time_out_s=0.2))

        self.rcs.pause_task()
        self.assertTrue(self.waiting_system_state(SystemState.PAUSE))
        self.rcs.stop()
        self.assertTrue(
            self.waiting_something('self.alarm_server.is_robot_lost_connection'), '等掉线失败'
        )
        self.rcs = RobotsControlSystem()
        self.rcs.start()
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.rcs.continue_task()
        self.assertFalse(self.waiting_system_state(SystemState.BUSY, time_out_s=0.3))

        for _ in range(10):
            self.rcs.move_to_pose(point)
            if self.waiting_system_state(SystemState.BUSY, time_out_s=0.5):
                break
        self.assertTrue(self.waiting_system_state(SystemState.BUSY), '老任务没有继续成功')
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertTrue(GeometryUtils.is_same_point(point, self.rcs.get_cur_point()))

    def test_move_with_new_path_and_speed(self):
        """测试追加路径变更速度"""
        paths_1 = [
            [
                SimplePoint(111760, 103821, 1, 100),
                SimplePoint(111394, 103821, 1, 100),
                SimplePoint(111028, 103821, 1, 100),
                SimplePoint(110295, 103821, 1, 100),
                SimplePoint(110295, 103998, 1, 100),
                SimplePoint(110295, 104175, 1, 100),
            ],
            [
                SimplePoint(110295, 104175, 0, 100),
                SimplePoint(110295, 110495, 0, 100),
            ],
        ]

        dst_point = HuaweiPoint(110295, 110495, 90000)
        cur_point = HuaweiPoint(111739, 103864, -179450)

        self.adapter_admin.set_sros_pose(
            Pose(cur_point.x / 1000, cur_point.y / 1000, cur_point.angle / 1000)
        )
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        # 初始多路段移动，限速 100
        self.rcs.move_multi_paths_with_no_payload(
            dst_point,
            points_groups=paths_1,
            task_id=12002,
            sub_task_id=1,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))

        # 等待走出贝塞尔路径
        breakpoint_1 = HuaweiPoint(110284, 104828, 91000)
        while not GeometryUtils.is_same_point(
            breakpoint_1, self.rcs.get_cur_point(), threshold=100
        ):
            time.sleep(0.2)

        # 初始多路段移动走出来贝赛尔后，发新直线移动，限速默认 1000
        self.rcs.move_to_pose(
            HuaweiPoint(110295, 110495, 90000),
            task_id=12002,
            sub_task_id=1,
            limit_v=1000,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))

        time.sleep(1)
        self.assertAlmostEqual(self.adapter_admin.get_sros_cur_v(), 1000, delta=10)

        dst_final = HuaweiPoint(110295, 114670, 90000)
        self.rcs.move_to_pose(
            dst_final,
            task_id=12002,
            sub_task_id=1,
            limit_v=800,
        )

        time.sleep(1)
        self.assertAlmostEqual(self.adapter_admin.get_sros_cur_v(), 800, delta=10)

        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertTrue(GeometryUtils.is_same_point(dst_final, self.rcs.get_cur_point()))

    def test_move_on_suspicious_bezier_path(self):
        """车在可疑贝塞尔末端的异常：
        1. 末端附近转圈
        2. 末端提前停止
        """

        paths = [
            [
                SimplePoint(110295, 104175, 1, 300),
                SimplePoint(110295, 103998, 1, 300),
                SimplePoint(110295, 103821, 1, 300),
                SimplePoint(111028, 103821, 1, 300),
                SimplePoint(111394, 103821, 1, 300),
                SimplePoint(111760, 103821, 1, 300),
            ]
        ]

        dst_point = HuaweiPoint(111760, 103821, 0)
        cur_point = HuaweiPoint(110293, 104175, -89954)

        self.adapter_admin.set_sros_pose(
            Pose(cur_point.x / 1000, cur_point.y / 1000, cur_point.angle / 1000)
        )
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        self.rcs.move_multi_paths_with_no_payload(
            dst_point,
            points_groups=paths,
            task_id=0,
            sub_task_id=255,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertTrue(GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point()))

    def test_plot_path_and_move_trace(self):
        """绘制路径和移动轨迹"""

        paths = [
            [
                SimplePoint(111760, 113954, 1, 200),
                SimplePoint(111394, 113954, 1, 200),
                SimplePoint(111028, 113954, 1, 200),
                SimplePoint(110295, 113954, 1, 200),
                SimplePoint(110295, 114122, 1, 200),
                SimplePoint(110295, 114290, 1, 200),
            ],
            [
                SimplePoint(110295, 114290, 0, 200),
                SimplePoint(110295, 114400, 0, 200),
            ],
        ]

        dst_point = HuaweiPoint(107779, 114400, 180000)
        cur_point = HuaweiPoint(111784, 113959, 179851)

        move_pose = [
            SimplePoint(111777, 113962, -1948),
            SimplePoint(111783, 113960, -1661),
            SimplePoint(111783, 113960, -1718),
            SimplePoint(111783, 113960, -1718),
            SimplePoint(111783, 113960, -1718),
            SimplePoint(111783, 113960, -1718),
            SimplePoint(111783, 113963, -3208),
            SimplePoint(111789, 113951, -41654),
            SimplePoint(111778, 113951, -81761),
            SimplePoint(111780, 113951, -121810),
            SimplePoint(111775, 113962, -165355),
            SimplePoint(111786, 113961, 179908),
            SimplePoint(111784, 113959, 179851),
            SimplePoint(111784, 113959, 179851),
            SimplePoint(111784, 113959, 179851),
            SimplePoint(111784, 113959, 179851),
            SimplePoint(111762, 113960, 179851),
            SimplePoint(111378, 113955, 179679),
            SimplePoint(110981, 113974, 176299),
            SimplePoint(110661, 114015, 166215),
            SimplePoint(110462, 114105, 145760),
            SimplePoint(110304, 114203, 163579),
            SimplePoint(110239, 114203, -157391),
            SimplePoint(110190, 114160, -118544),
            SimplePoint(110180, 114095, -79641),
            SimplePoint(110207, 114042, -40622),
            SimplePoint(110266, 114019, -1718),
            SimplePoint(110333, 114038, 37414),
            SimplePoint(110376, 114083, 80328),
            SimplePoint(110372, 114097, 96142),
            SimplePoint(110366, 114137, 105768),
            SimplePoint(110302, 114238, 144442),
            SimplePoint(110236, 114263, -172689),
            SimplePoint(110185, 114233, -133900),
            SimplePoint(110160, 114185, -94767),
            SimplePoint(110175, 114130, -55863),
            SimplePoint(110184, 114100, -43201),
            SimplePoint(110184, 114100, -43258),
            SimplePoint(110184, 114100, -43258),
            SimplePoint(110184, 114100, -43258),
            SimplePoint(110184, 114100, -43258),
            SimplePoint(110184, 114100, -43258),
        ]

        # 检查绘制路径与轨迹
        create_task_and_plot_path_from_points(
            paths,
            dst_point,
            cur_point,
            move_pose,
            save_to='task_path.png',
        )


if __name__ == '__main__':
    unittest.main()
