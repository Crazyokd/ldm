#!/usr/bin/python3
# Copyright 2024 Standard Robots Co. All rights reserved.
import time
import unittest
import logging

from protocol_adapter.models.state import SystemState
from protocol_adapter.huawei_model.const import (
    ShelfAnglePolicy,
    AdjustType,
    LockSpaceType,
    DetectType,
    MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF,
    MSG_REQ_LINEAR_MOVE_AFTER_RAISE_SHELF,
)
from protocol_adapter.huawei_model.point import Point as HuaweiPoint, SimplePoint
from protocol_adapter.protobuf_wrapper.base import Pose, Point
from protocol_adapter.adapter_admin import AdapterAdmin
from protocol_adapter.mock.world_mock import WorldMock
from protocol_adapter.const import DeviceType
from protocol_adapter.utils import AngleUtils, GeometryUtils

from test.robots_control_system import RobotsControlSystem
from test.alarm_server import AlarmServer

_logger = logging.getLogger(__name__)

SHELF_ID_STR = '000F0101010331'  # 货架ID


class LiftRotateTest(unittest.TestCase):
    """旋转顶升车相关的测试"""

    def setUp(self):
        self.alarm_server = AlarmServer()
        self.rcs = RobotsControlSystem()
        self.rcs.start()
        self.adapter_admin = AdapterAdmin(mock=True, device_type=DeviceType.RISER)
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
                    f' {self.rcs.get_cur_point()}, {self.rcs.shelf_angle}'
                )
            if curr_state.value == state.value:
                return True
        return False

    def test_not_shelf_id_detect(self):
        """测试探测不到货架，根据探测类型上报状态"""
        point = self.rcs.get_cur_point()
        continue_time = 2
        self.rcs.shelf_sn_detect(point, continue_time, detect_type=DetectType.Default)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        point2 = HuaweiPoint(0, 0, 90000)
        self.rcs.shelf_sn_detect(point2, continue_time, detect_type=DetectType.NotFoundWarning)
        self.waiting_system_state(SystemState.BUSY, time_out_s=1)
        self.assertTrue(self.waiting_system_state(SystemState.SCAN_ERROR))

    def test_shelf_id_detect(self):
        world = WorldMock()
        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 0))
        shelf_point = HuaweiPoint(0, 0, 0)
        self.rcs.shelf_sn_detect(shelf_point, 8)
        time.sleep(0.1)
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        for _ in range(40):
            time.sleep(0.1)
            if self.rcs.actuator_shelf_id_str:
                break
        self.assertEqual(self.rcs.actuator_shelf_id_str, SHELF_ID_STR)

    def test_raise_and_raise_again_with_another_angle(self):
        """测试顶升任务后，再次给不同角度顶升
        关联问题：两次顶升角度不同，导致锁空间申请不通过
        """

        world = WorldMock()
        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 90))
        shelf_point = HuaweiPoint(0, 0, 90000)

        self.rcs.raise_shelf_action(
            shelf_point, SHELF_ID_STR, adjust_type=AdjustType.NO_ROTATE_EXECUTOR
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        # 验证扫码匹配
        self.assertEqual(self.rcs.actuator_shelf_id_str, SHELF_ID_STR)

        shelf_point2 = HuaweiPoint(0, 0, 180000)
        self.rcs.raise_shelf_action(
            shelf_point2, SHELF_ID_STR, adjust_type=AdjustType.NO_ROTATE_EXECUTOR
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        # 另外最终小车和货架角度
        point1 = self.rcs.get_cur_point()
        assert GeometryUtils.is_same_point(point1, shelf_point2)
        shelf_id, shelf_pose = world.get_shelf_by_point(Point(0, 0))
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertAlmostEqual(shelf_pose.yaw, 90, 1)

    def test_raise_and_stop_after_raise(self):
        """测试顶升任务后下发停止操作，预期正常上报空闲状态
        关联问题：ldm下发停止指令后，触发获取设备状态的异常，需要重启恢复
        """

        world = WorldMock()
        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 90))
        shelf_point = HuaweiPoint(0, 0, 90000)

        self.rcs.raise_shelf_action(shelf_point, SHELF_ID_STR)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        # 验证扫码匹配
        self.assertEqual(self.rcs.actuator_shelf_id_str, SHELF_ID_STR)

        # 模拟下发停止移动，并等待下车停止移到恢复空闲状态
        self.rcs.stop_move()
        self.assertFalse(self.waiting_system_state(SystemState.NONE, time_out_s=1))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE, time_out_s=1))

        # 另外验证没动
        point1 = self.rcs.get_cur_point()
        self.assertTrue(
            GeometryUtils.is_same_point(point1, shelf_point), f'{point1} vs {shelf_point}'
        )

    def test_scan_shelf_and_replace_shelf_before_raise_shelf(self):
        """测试货架扫码后人为替换货架的情况
        对应场景：ldm 下发去站点扫码，顶货架然后移动的任务
        1. 小车去站点扫码，然后向 ldm 上报货架码
        2. ldm 按上报的二维码下发顶升移动的任务
        3. 小车顶升前，人为替换二维码
        4. 小车应该上报二维码异常停在那里
        """
        world = WorldMock()

        # 摆货架
        world.set_shelf(SHELF_ID_STR, Pose(1, 0, 90))
        shelf_point = HuaweiPoint(1000, 0, 0)

        _logger.info('下发去站点扫码任务: 预期先移动到站点，然后扫码')
        self.rcs.shelf_sn_detect(shelf_point, continue_time=2)

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        _logger.info('已扫码，使用错误的二维码下发顶升任务(模拟二维码被替换)')
        self.rcs.raise_shelf_action(shelf_point, SHELF_ID_STR[2:])

        _logger.info('等待小车扫码发现异常，上报异常状态..')
        # 扫码发现异常会持续重试，不影响异常上报
        self.waiting_system_state(SystemState.BUSY, time_out_s=0.4)
        self.assertTrue(self.waiting_system_state(SystemState.SHELF_SN_ERROR, time_out_s=2))
        # 扫到的应该还是前面放的码
        self.assertEqual(self.rcs.actuator_shelf_id_str, SHELF_ID_STR)

    def test_raise_shelf_move_and_putdown_shelf(self):
        """测试背起货架，然后移动，最后放下货架"""
        world = WorldMock()
        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 0))
        shelf_point = HuaweiPoint(0, 0, 0)
        self.rcs.raise_shelf_action(shelf_point, SHELF_ID_STR)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertEqual(self.rcs.actuator_shelf_id_str, SHELF_ID_STR)

        point = HuaweiPoint(2000, 0, 0)
        self.rcs.move_to_pose_with_shelf(
            point,
            shelf_moving_policy=0,
            shelf_target_angle=0,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.rcs.put_down_shelf_action(point)
        self.assertTrue(self.waiting_system_state(SystemState.EXECUTE_ACTION))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        shelf_id = world.get_shelf(Pose(2, 0, 0))
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertTrue(GeometryUtils.is_same_point(point, self.rcs.get_cur_point()))

    def test_raise_shelf_move_with_shelf_vertical(self):
        """测试背起货架，然后背着货架横着走的情况"""
        world = WorldMock()
        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 0))
        shelf_point = HuaweiPoint(0, 0, 0)
        self.rcs.raise_shelf_action(shelf_point, SHELF_ID_STR)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertEqual(self.rcs.actuator_shelf_id_str, SHELF_ID_STR)

        point = HuaweiPoint(2000, 0, 0)
        self.rcs.move_to_pose_with_shelf(
            point,
            shelf_moving_policy=90000,
            shelf_target_angle=90000,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        shelf_id = world.get_shelf(Pose(2, 0, 90))
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertTrue(GeometryUtils.is_same_point(point, self.rcs.get_cur_point()))

    def test_no_rotate_and_put_shelf_with_small_angle(self):
        """测试放货架后顶板微调，角度小直接调"""
        init_pose = Pose(20.22, 16.02, -90.8)
        shelf_pose = Pose(20.22, 16.02, -182.2)
        self.adapter_admin.set_sros_pose(init_pose, shelf_pose=shelf_pose, shelf_id=SHELF_ID_STR)
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        dst_point = HuaweiPoint(20220, 16020, -90000)
        self.rcs.put_down_shelf_action(
            dst_point, adjust_type=AdjustType.NO_ANGLE_TO_SHELF_NO_ROTATE_EXECUTOR
        )

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        # 顶板回归最近的 90n 方向，相对 -90 度(与原来一致)
        assert AngleUtils.equal_norm(self.adapter_admin.get_sros_plate_angle(), -90, 0.1)

    def test_no_rotate_and_put_shelf_with_large_angle(self):
        """测试放货架后顶板微调，角度大不调"""
        init_pose = Pose(20.22, 16.02, -90.8)
        shelf_pose = Pose(20.22, 16.02, -97.64)
        self.adapter_admin.set_sros_pose(init_pose, shelf_pose=shelf_pose, shelf_id=SHELF_ID_STR)
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        dst_point = HuaweiPoint(20220, 16020, -90000)
        self.rcs.put_down_shelf_action(
            dst_point, adjust_type=AdjustType.NO_ANGLE_TO_SHELF_NO_ROTATE_EXECUTOR
        )

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        # 顶板小车角度过大，保持原先的相对角度(区分方向)
        assert AngleUtils.equal_norm(
            self.adapter_admin.get_sros_plate_angle(), shelf_pose.yaw - init_pose.yaw, 0.1
        )

    def test_put_shelf_and_move(self):
        """测试放下货架叠加移动任务
        全过程：
        1. 起点顶货架
        2. 移动去终点
        3. 发放下货架叠加移动指令回起点
        """
        world = WorldMock()

        # 摆货架
        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 0))
        start_point = HuaweiPoint(0, 0, 0)
        end_point = HuaweiPoint(1000, 0, 0)

        _logger.debug('>> 1. 起点顶货架')
        self.rcs.raise_shelf_action(start_point, SHELF_ID_STR)

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        _logger.debug('>> 2. 移动去终点')
        self.rcs.move_to_pose_with_shelf(end_point)

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.assertTrue(GeometryUtils.is_same_point(end_point, self.rcs.get_cur_point()))

        _logger.debug('>> 3. 发放下货架叠加移动指令回起点')
        self.rcs.put_down_shelf_and_move(start_point)

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.assertTrue(GeometryUtils.is_same_point(start_point, self.rcs.get_cur_point()))

    def test_put_shelf_and_move_with_no_shelf(self):
        """测试放下货架叠加移动任务，但任务开始时并无货架
        全过程：
        1. 起点顶货架
        2. 移动去终点
        3. 放下货架
        4. 发放下货架叠加移动指令回起点

        这里允许第 4 步中忽略已经放下货架的异常
        """
        world = WorldMock()

        # 摆货架
        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 0))
        start_point = HuaweiPoint(0, 0, 0)
        end_point = HuaweiPoint(1000, 0, 0)

        _logger.debug('>> 1. 起点顶货架')
        self.rcs.raise_shelf_action(start_point, SHELF_ID_STR)

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        _logger.debug('>> 2. 移动去终点')
        self.rcs.move_to_pose_with_shelf(end_point)

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.assertTrue(GeometryUtils.is_same_point(end_point, self.rcs.get_cur_point()))

        _logger.debug('>> 3. 放下货架')
        self.rcs.put_down_shelf_action(end_point)

        self.assertTrue(self.waiting_system_state(SystemState.EXECUTE_ACTION))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.assertTrue(GeometryUtils.is_same_point(end_point, self.rcs.get_cur_point()))

        _logger.debug('>> 4. 发放下货架叠加移动指令回起点')
        self.rcs.put_down_shelf_and_move(start_point)

        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.assertTrue(GeometryUtils.is_same_point(start_point, self.rcs.get_cur_point()))

    def test_raise_shelf_move_with_shelf_offset_4deg_and_100mm(self):
        """测试货架摆偏(100mm, 4deg)，顶起货架并移动的情况。
        预期行为：
        1. 133 扫货架，410 顶升(顶升完小车与货架方向一致)
        2. 原地小角度调整货架: 开同步旋转，小车转回座标轴方向，关同步旋转, 412 调货架
        3. 自动调整直线移动到站点 (# TODO: zz: 目前没有第三步，调完角度不调偏差?? 待确定逻辑)
        4. 执行后续移动任务
        """

        world = WorldMock()

        # 放货架：偏离站点 100mm, 4deg
        world.set_shelf(SHELF_ID_STR, Pose(0.1, 0, 90 + 4))

        # 下发到指定座标(station)顶货架的任务
        task_position = HuaweiPoint(0, 0, 90000)
        self.rcs.raise_shelf_action(task_position, SHELF_ID_STR)

        # 等待小车执行任务: 1, 2, 3
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        # 检测顶起货架后的状态
        shelf_id, shelf_pose = world.get_shelf_by_point(Point(0, 0))
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertAlmostEqual(shelf_pose.yaw, 90, 1)
        self.assertTrue(GeometryUtils.is_same_point(task_position, self.rcs.get_cur_point()))

        # 顶起货架调整完毕后，下发移动任务
        point = HuaweiPoint(0, 2000, 0)
        self.rcs.move_to_pose_with_shelf(
            point,
            shelf_moving_policy=0,
            shelf_target_angle=90000,
        )

        # 等待小车执行任务: 4
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        # 检测任务终了状态
        shelf_id, shelf_pose = world.get_shelf_by_point(Point(0, 2))
        self.assertAlmostEqual(shelf_pose.yaw, 90, 1)
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertTrue(GeometryUtils.is_same_point(point, self.rcs.get_cur_point()))

    def test_raise_shelf_move_with_shelf_offset_300mm(self):
        """
        测试货架摆偏300mm > 200mm，下发顶起货架移动任务

        预期行为：
        - ldm 下发任务: 0x312
        1. 133 扫货架，410 顶升(顶升完小车与货架方向一致)
        2. 检测到位置偏移过大，上报异常，不移动
        """

        world = WorldMock()

        # 放货架：偏离站点 300mm
        world.set_shelf(SHELF_ID_STR, Pose(0.3, 0, 90))

        # 下发到指定座标(station)顶货架的任务
        task_position = HuaweiPoint(0, 0, 90000)
        self.rcs.raise_shelf_action(task_position, SHELF_ID_STR, shelf_target_angle=90000)

        # 等待小车执行任务: 1
        self.waiting_system_state(SystemState.BUSY, 0.2)
        self.assertTrue(self.waiting_system_state(SystemState.SHELF_OFFSET_ERROR))

        # 检测顶起货架后的状态
        shelf_id, shelf_pose = world.get_shelf_by_point(Point(0, 0))
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertAlmostEqual(shelf_pose.yaw, 90, 1)

        # TODO: zz: 目前的异常逻辑与任务关联，任务存在，才有关联到任务的异常，
        #   顶完货架后的移动已经是另一个独立任务，如果调度无视之前动作的异常发新任务，
        #   小车应当就新任务的执行条件重新检查，重新上报对应的异常
        #   基本逻辑：异常来自执行条件与执行结果的检测，不受之前任务状态影响

        # 下发移动任务
        point = HuaweiPoint(0, 2000, 0)
        self.rcs.move_to_pose_with_shelf(
            point,
            type_code=MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF,
            shelf_moving_policy=ShelfAnglePolicy.Parallel,
            shelf_target_angle=90000,
            points_groups=[
                [SimplePoint(0, 0, 0), SimplePoint(0, 2000, 0)],
            ],
        )

        # 此时到路径距离偏差超限，应当报告异常，原地不动不接受移动任务
        self.assertTrue(self.waiting_system_state(SystemState.NAV_OFF_PATH))

        # 检测任务终了状态：停在之前货架偏移的位置
        self.assertAlmostEqual(shelf_pose.yaw, 90, 1)
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertTrue(
            GeometryUtils.is_same_point(HuaweiPoint(0.3, 0, 90000), self.rcs.get_cur_point())
        )

    def test_raise_shelf_move_with_shelf_offset_10deg_no_lock_space(self):
        """
        测试货架摆偏 10 > 5 度，移动时检查锁角度偏差，报角度异常不移动

        预期行为：
        1. 133 扫货架，410 顶升(顶升完小车与货架方向一致)
        2. 移动前判断锁空间，锁空间本地检查不通过，卡住，报角度异常
        """

        world = WorldMock()

        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 90 + 10))

        # 下发到指定座标(station)顶货架的任务
        task_position = HuaweiPoint(0, 0, 90000)
        self.rcs.raise_shelf_action(
            task_position,
            SHELF_ID_STR,
            shelf_target_angle=90000,
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
        )

        # 等待小车执行任务: 1
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        # 检测顶起货架后的状态
        shelf_id, shelf_pose = world.get_shelf_by_point(Point(0, 0))
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertAlmostEqual(shelf_pose.yaw, 90 + 10, 1)

        # 下发移动任务
        point = HuaweiPoint(0, 2000, 0)
        self.rcs.move_to_pose_with_shelf(
            point,
            shelf_moving_policy=ShelfAnglePolicy.Parallel,
            shelf_target_angle=90000,
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
        )

        self.waiting_system_state(SystemState.BUSY, 0.2)
        # 此时距离偏差超限，应当报告异常，原地不动不接受移动任务
        self.assertTrue(self.waiting_system_state(SystemState.SHELF_ANGLE_ERROR))

        # 检测任务终了状态：停在之前货架偏移的位置
        self.assertAlmostEqual(shelf_pose.yaw, 90 + 10, 1)
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertTrue(
            GeometryUtils.is_same_point(HuaweiPoint(0, 0, 100000), self.rcs.get_cur_point())
        )

    def test_raise_shelf_move_with_shelf_is_tilted_10_deg_and_lock_space_accept(self):
        """测试货架摆偏10°且可以锁空间的情况下，顶起货架并移动的情况。期望先将货架摆正然后再移动"""
        world = WorldMock()
        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 90 + 10))
        shelf_point = HuaweiPoint(0, 0, 90000)
        self.rcs.raise_shelf_action(shelf_point, SHELF_ID_STR)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertEqual(self.rcs.actuator_shelf_id_str, SHELF_ID_STR)

        point = HuaweiPoint(0, 2000, 0)
        self.rcs.move_to_pose_with_shelf(
            point,
            shelf_moving_policy=0,
            shelf_target_angle=90000,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        shelf_id, shelf_pose = world.get_shelf_by_point(Point(0, 2))
        self.assertAlmostEqual(shelf_pose.yaw, 90, 1)
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertTrue(GeometryUtils.is_same_point(point, self.rcs.get_cur_point()))

    def test_raise_shelf_move_with_shelf_is_tilted_11_deg_and_lock_space_for_shelf_reject(
        self,
    ):
        """测试货架摆偏11°且锁空间不允许摆货架的情况下，顶起货架并移动的情况。期望停在那里不允许移动。
        测试点：锁空间失败会停在那里"""
        world = WorldMock()
        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 90 + 11))
        self.rcs.set_allow_lock_space_rule(
            {
                HuaweiPoint(0, 0, 90000): [
                    LockSpaceType.NO_PAYLOAD_ROTATE,
                    LockSpaceType.RECT_ROTATE,
                ]
            }
        )
        self.rcs.set_allow_lock_space_default(False)
        shelf_point = HuaweiPoint(0, 0, 90000)
        self.rcs.raise_shelf_action(shelf_point, SHELF_ID_STR)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertEqual(self.rcs.actuator_shelf_id_str, SHELF_ID_STR)

        point = HuaweiPoint(0, 2000, 0)
        self.rcs.move_to_pose_with_shelf(
            point,
            shelf_moving_policy=0,
            shelf_target_angle=90000,
        )
        self.waiting_system_state(SystemState.BUSY, 0.2)
        self.assertTrue(self.waiting_system_state(SystemState.LOCK_SPACE_FAILED_PERMANENT))

        shelf_id, shelf_pose = world.get_shelf_by_point(Point(0, 0))
        self.assertAlmostEqual(shelf_pose.yaw, 90 + 11)
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertTrue(
            GeometryUtils.is_same_point(HuaweiPoint(0, 0, 90000), self.rcs.get_cur_point())
        )

    def test_raise_shelf_move_with_shelf_is_tilted_4_deg_and_lock_space_for_shelf_reject(
        self,
    ):
        """测试货架摆偏4°且锁空间不允许摆货架的情况下，顶起货架并移动的情况。期望小于5°的矫正可以不用申请旋转"""
        world = WorldMock()
        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 90 + 4))
        self.rcs.set_allow_lock_space_rule(
            {
                HuaweiPoint(0, 0, 90000): [
                    LockSpaceType.NO_PAYLOAD_ROTATE,
                    LockSpaceType.RECT_ROTATE,
                ]
            }
        )
        self.rcs.set_allow_lock_space_default(False)
        shelf_point = HuaweiPoint(0, 0, 90000)
        self.rcs.raise_shelf_action(shelf_point, SHELF_ID_STR)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertEqual(self.rcs.actuator_shelf_id_str, SHELF_ID_STR)

        point = HuaweiPoint(0, 2000, 90000)
        self.rcs.move_to_pose_with_shelf(
            point,
            shelf_moving_policy=0,
            shelf_target_angle=90000,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        shelf_id, shelf_pose = world.get_shelf_by_point(Point(0, 2))
        self.assertAlmostEqual(shelf_pose.yaw, 90, 1)
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertTrue(GeometryUtils.is_same_point(point, self.rcs.get_cur_point()))

    def test_raise_and_move_shelf_with_offset_9deg(self):
        """
        货架角度偏差 9 度，但是允许 LockSpaceType.RECT_ROTATE，应当允许旋转调整
        """
        world = WorldMock()
        world.set_shelf(SHELF_ID_STR, Pose(0, 0, 90 + 9))
        self.rcs.set_allow_lock_space_rule(
            {
                HuaweiPoint(0, 0, 90000): [
                    LockSpaceType.NO_PAYLOAD_ROTATE,
                    LockSpaceType.RECT_ROTATE,
                ]
            }
        )
        self.rcs.set_allow_lock_space_default(False)
        shelf_point = HuaweiPoint(0, 0, 90000)
        self.rcs.raise_shelf_action(shelf_point, SHELF_ID_STR)
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertEqual(self.rcs.actuator_shelf_id_str, SHELF_ID_STR)

        point = HuaweiPoint(0, 2000, 90000)
        self.rcs.move_to_pose_with_shelf(
            point,
            shelf_moving_policy=0,
            shelf_target_angle=90000,
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
        )
        self.waiting_system_state(SystemState.BUSY, 0.2)
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        shelf_id, shelf_pose = world.get_shelf_by_point(Point(0, 2))
        self.assertAlmostEqual(shelf_pose.yaw, 90, 1)
        self.assertEqual(shelf_id, SHELF_ID_STR)
        self.assertTrue(GeometryUtils.is_same_point(point, self.rcs.get_cur_point()))

    def test_move_with_shelf_on_bezier_offline_path(self):
        """
        测试偏离路网后，多路径载货移动任务响应情况
        关联问题：
            之前偏离贝塞尔路径后，小车从当前位置规划新贝塞尔路径，导致旋转货架
            目前修改沿原贝塞尔移动(起点调整)，依靠导航自动回归
        """
        init_pose = Pose(48.039, 299.901, -90.871)
        self.adapter_admin.set_sros_pose(init_pose, shelf_pose=init_pose, shelf_id=SHELF_ID_STR)
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        dst_point = HuaweiPoint(47920, 293410, -90000)
        self.rcs.move_to_pose_with_shelf(
            dst_point,
            shelf_moving_policy=0,
            shelf_target_angle=270000,
            points_groups=[
                [
                    SimplePoint(46340, 301084, 1),
                    SimplePoint(46735, 301084, 1),
                    SimplePoint(47130, 301084, 1),
                    SimplePoint(47920, 301084, 1),
                    SimplePoint(47920, 300313, 1),
                    SimplePoint(47920, 299541, 1),
                ],
                [
                    SimplePoint(47920, 299541, 0),
                    SimplePoint(47920, 293410, 0),
                ],
            ],
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            task_id=2,
            sub_task_id=1,
            type_code=MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.assertTrue(GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point()))

    def test_check_lockspace_rotate_180_on_bezier_without_delta(self):
        """
        测试贝塞尔路径上移动前小车带货架 180 度旋转问题(货架小车相对角度不需要调整货架)

        问题：小车载货架向货架反方向移动中，如果前面有条贝塞尔路径，且小车在路径前有手动重启，
            ldm在小车重启后继续发重启前的多路段贝塞尔路线，小车在货架零度方向重新顶升，然后带
            货架原地直接旋转180度
        """
        init_pose = Pose(117.883, 102.632, -5.729)
        self.adapter_admin.set_sros_pose(init_pose, shelf_pose=init_pose, shelf_id=SHELF_ID_STR)
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        init_point = self.rcs.get_cur_point()

        dst_point = HuaweiPoint(116472, 108449, 90000)
        self.rcs.move_to_pose_with_shelf(
            dst_point,
            shelf_moving_policy=0,
            shelf_target_angle=90000,
            points_groups=[
                [
                    SimplePoint(117892, 102643, 1),
                    SimplePoint(117537, 102643, 1),
                    SimplePoint(117182, 102643, 1),
                    SimplePoint(116472, 102643, 1),
                    SimplePoint(116472, 103229, 1),
                    SimplePoint(116472, 103814, 1),
                ],
                [
                    SimplePoint(116472, 103814, 0),
                    SimplePoint(116472, 108449, 0),
                ],
            ],
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            task_id=2,
            sub_task_id=1,
            type_code=MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF,
        )
        self.assertTrue(self.waiting_system_state(SystemState.TASK_WRONG_ANGLE))
        self.assertTrue(GeometryUtils.is_same_point(init_point, self.rcs.get_cur_point()))

    def test_check_lockspace_rotate_180_on_bezier_with_delta(self):
        """
        测试贝塞尔路径上移动前小车带货架 180 度旋转问题(货架小车相对角度需要调整货架)

        问题：小车载货架向货架反方向移动中，如果前面有条贝塞尔路径，且小车在路径前有手动重启，
            ldm在小车重启后继续发重启前的多路段贝塞尔路线，小车在货架零度方向重新顶升，然后带
            货架原地直接旋转180度
        """
        init_pose = Pose(117.908, 127.646, -1.031)
        self.adapter_admin.set_sros_pose(init_pose, shelf_pose=init_pose, shelf_id=SHELF_ID_STR)
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        init_point = self.rcs.get_cur_point()

        dst_point = HuaweiPoint(116472, 133554, 90000)
        self.rcs.move_to_pose_with_shelf(
            dst_point,
            shelf_moving_policy=180000,
            shelf_target_angle=270000,
            points_groups=[
                [
                    SimplePoint(117897, 127643, 1, 300),
                    SimplePoint(117541, 127643, 1, 300),
                    SimplePoint(117185, 127643, 1, 300),
                    SimplePoint(116472, 127643, 1, 300),
                    SimplePoint(116472, 127991, 1, 300),
                    SimplePoint(116472, 128338, 1, 300),
                ],
                [SimplePoint(116472, 128338, 0, 300), SimplePoint(116472, 128814, 0, 300)],
                [SimplePoint(116472, 128814, 0, 300), SimplePoint(116472, 132419, 0, 300)],
                [SimplePoint(116472, 132419, 0, 300), SimplePoint(116472, 133554, 0, 300)],
            ],
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            task_id=2,
            sub_task_id=1,
            type_code=MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF,
        )
        self.assertTrue(self.waiting_system_state(SystemState.TASK_WRONG_ANGLE))
        self.assertTrue(GeometryUtils.is_same_point(init_point, self.rcs.get_cur_point()))

    def test_raise_shelf_move_with_shelf_is_tilted_11_deg_and_adjust_type_reject(
        self,
    ):
        """
        测试货架摆偏11°且调整类型不允许摆货架的情况下，顶起货架并移动的情况。
        期望停在那里不允许移动,其中刚出现多条移动任务的第一条位置移动路径为短直线
        测试点：
            1.移动任务只有一条很短的执行，但货架角度不对的情况下，允许移动。（主要场景为顶起货架后回归路网）
            2.有多条移动路径，但第一条为很短的直线，不允许移动
            3.移动任务前，货架角度不对，当adjust_type不允许调整时，应该停在那里
        """
        self.adapter_admin.set_sros_pose(Pose(100.076, 133.484, 180))
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置
        world = WorldMock()
        world.set_shelf(SHELF_ID_STR, Pose(100.130, 133.438, 101.111))
        self.rcs.set_allow_lock_space_rule(
            {
                HuaweiPoint(100076, 133484, 180000): [
                    LockSpaceType.NO_PAYLOAD_ROTATE,
                    LockSpaceType.RECT_ROTATE,
                ]
            }
        )
        self.rcs.set_allow_lock_space_default(False)
        shelf_point = HuaweiPoint(100076, 133484, 180000)
        self.rcs.raise_shelf_action(
            shelf_point,
            SHELF_ID_STR,
            shelf_moving_policy=ShelfAnglePolicy.Ignore,
            shelf_target_angle=90000,
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            task_id=2,
            sub_task_id=0,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertEqual(self.rcs.actuator_shelf_id_str, SHELF_ID_STR)

        dst_point1 = HuaweiPoint(100130, 133438, 90000)
        self.rcs.move_to_pose_with_shelf(
            dst_point1,
            shelf_moving_policy=0,
            shelf_target_angle=90000,
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            task_id=2,
            sub_task_id=0,
        )
        # 这里的角度异常是目标点调方向时不通过，但前面会移动
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.SHELF_ANGLE_ERROR))

        dst_point2 = HuaweiPoint(105276, 135482, 0)
        self.rcs.move_to_pose_with_shelf(
            dst_point2,
            shelf_moving_policy=0,
            shelf_target_angle=0,
            points_groups=[
                [SimplePoint(100076, 133474, 0), SimplePoint(100076, 133484, 0)],
                [
                    SimplePoint(100076, 133484, 1),
                    SimplePoint(100076, 134483, 1),
                    SimplePoint(100076, 135482, 1),
                    SimplePoint(100988, 135482, 1),
                    SimplePoint(101443, 135482, 1),
                    SimplePoint(101899, 135482, 1),
                ],
                [SimplePoint(101899, 135482, 0), SimplePoint(105276, 135482, 0)],
            ],
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            task_id=2,
            sub_task_id=1,
            type_code=MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF,
        )
        self.waiting_system_state(SystemState.BUSY, 0.2)
        self.assertTrue(self.waiting_system_state(SystemState.SHELF_ANGLE_ERROR))

        shelf_id, shelf_pose = world.get_shelf_by_point(
            Point(dst_point1.x / 1000, dst_point1.y / 1000)
        )
        self.assertAlmostEqual(shelf_pose.yaw, 101.111, delta=1)
        self.assertEqual(shelf_id, SHELF_ID_STR)
        cur_pose = self.rcs.get_cur_point()
        self.assertAlmostEqual(dst_point1.x, cur_pose.x, delta=100)
        self.assertAlmostEqual(dst_point1.y, cur_pose.y, delta=100)

    def test_shelf_angle_error_will_stop_multi_path_move_if_lock_reject(self):
        """货架和车偏差11°，启动多路径任务，且不允许锁空间的情况下，车应该停在那里"""
        self.adapter_admin.set_sros_pose(
            Pose(96.959, 141.438, 6.073),
            shelf_pose=Pose(96.959, 141.438, -4.584),
            shelf_id=SHELF_ID_STR,
        )
        time.sleep(1)  # 等待适配器和调度都更新车的位置
        world = WorldMock()
        shelf_id, shelf_pose = world.get_shelf_by_point(Point(96.959, 141.438))
        self.assertAlmostEqual(shelf_pose.yaw, AngleUtils.normalize_360(-4.584), delta=1)
        self.rcs.set_allow_lock_space_default(False)
        dst_point = HuaweiPoint(101840, 141390, 0)
        self.rcs.move_to_pose_with_shelf(
            dst_point,
            shelf_moving_policy=0,
            shelf_target_angle=0,
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            points_groups=[
                [
                    SimplePoint(95682, 139043, 1),
                    SimplePoint(95682, 140217, 1),
                    SimplePoint(95682, 141390, 1),
                    SimplePoint(96440, 141390, 1),
                    SimplePoint(96819, 141390, 1),
                    SimplePoint(97198, 141390, 1),
                ],
                [SimplePoint(97198, 141390, 0), SimplePoint(101840, 141390, 0)],
            ],
            type_code=MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF,
        )
        # 转角度的动作，可能等到，也可能等不到，取决于转的角度大小
        self.waiting_system_state(SystemState.BUSY, 0.1)
        self.assertTrue(self.waiting_system_state(SystemState.SHELF_ANGLE_ERROR))

        world = WorldMock()
        shelf_id, shelf_pose = world.get_shelf_by_point(Point(96.959, 141.438))
        self.assertEqual(shelf_id, SHELF_ID_STR)
        cur_pose = self.rcs.get_cur_point()
        self.assertAlmostEqual(96959, cur_pose.x, delta=100)
        self.assertAlmostEqual(141438, cur_pose.y, delta=100)

    def test_shelf_angle_error_will_move_multi_path_move_if_lock_accept(self):
        """货架和车偏差11°，启动多路径任务，且允许锁空间的情况下，期望摆正货架再执行移动任务"""
        self.adapter_admin.set_sros_pose(
            Pose(96.959, 141.438, 6.073),
            shelf_pose=Pose(96.959, 141.438, -4.584),
            shelf_id=SHELF_ID_STR,
        )
        time.sleep(1)  # 等待适配器和调度都更新车的位置
        world = WorldMock()
        shelf_id, shelf_pose = world.get_shelf_by_point(Point(96.959, 141.438))
        self.assertAlmostEqual(shelf_pose.yaw, AngleUtils.normalize_360(-4.584), delta=1)
        dst_point = HuaweiPoint(101840, 141390, 0)
        self.rcs.move_to_pose_with_shelf(
            dst_point,
            shelf_moving_policy=0,
            shelf_target_angle=0,
            points_groups=[
                [
                    SimplePoint(95682, 139043, 1),
                    SimplePoint(95682, 140217, 1),
                    SimplePoint(95682, 141390, 1),
                    SimplePoint(96440, 141390, 1),
                    SimplePoint(96819, 141390, 1),
                    SimplePoint(97198, 141390, 1),
                ],
                [SimplePoint(97198, 141390, 0), SimplePoint(101840, 141390, 0)],
            ],
            type_code=MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        world = WorldMock()
        shelf_id, shelf_pose = world.get_shelf_by_point(
            Point(dst_point.x / 1000, dst_point.y / 1000)
        )
        self.assertEqual(shelf_id, SHELF_ID_STR)
        cur_pose = self.rcs.get_cur_point()
        self.assertAlmostEqual(dst_point.x, cur_pose.x, delta=100)
        self.assertAlmostEqual(dst_point.y, cur_pose.y, delta=100)
        self.assertAlmostEqual(dst_point.angle, cur_pose.angle, delta=100)

    def test_multi_path_task_origin_short_path_regression(self):
        """测试路径替换，同一个任务ID，路径类型变更也需要正常无缝替换"""
        self.adapter_admin.set_sros_pose(
            Pose(114.103, 139.041, 90.985),
            shelf_pose=Pose(114.103, 139.041, 90.985),
            shelf_id='T3003035',
        )
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置
        dst_point = HuaweiPoint(109797, 142390, 180000)
        self.rcs.move_to_pose_with_shelf(
            dst_point,
            shelf_moving_policy=0,
            shelf_target_angle=180000,
            points_groups=[
                [SimplePoint(114054, 139043, 0), SimplePoint(114054, 141390, 0)],
                [
                    SimplePoint(114054, 141390, 1),
                    SimplePoint(114054, 141890, 1),
                    SimplePoint(114054, 142390, 1),
                    SimplePoint(113474, 142390, 1),
                    SimplePoint(113184, 142390, 1),
                    SimplePoint(112894, 142390, 1),
                ],
                [SimplePoint(112894, 142390, 0), SimplePoint(109797, 142390, 0)],
            ],
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            type_code=MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        self.assertTrue(
            GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point()), '没有到达最终目标点'
        )

    def test_off_path_state_report(self):
        """收到移动任务，如果小车在路径外时，应当报偏航"""
        init_pose = Pose(103.982, 80.298, 89.094)
        self.adapter_admin.set_sros_pose(
            init_pose,
            shelf_pose=init_pose,
            shelf_id='T3003248',
        )
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        dst_point = HuaweiPoint(106990, 85610, 0)
        path = [
            [SimplePoint(103985, 80600, 0, 600), SimplePoint(103985, 84609, 0, 600)],
            [
                SimplePoint(103985, 84609, 1, 300),
                SimplePoint(103985, 85110, 1, 300),
                SimplePoint(103985, 85610, 1, 300),
                SimplePoint(104679, 85610, 1, 300),
                SimplePoint(105025, 85610, 1, 300),
                SimplePoint(105372, 85610, 1, 300),
            ],
            [SimplePoint(105372, 85610, 0, 600), SimplePoint(106990, 85610, 0, 600)],
        ]

        self.rcs.move_to_pose_with_shelf(
            dst_point,
            shelf_moving_policy=0,
            shelf_target_angle=0,
            points_groups=path,
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            type_code=MSG_REQ_LINEAR_MULTI_PATH_MOVE_AFTER_RAISE_SHELF,
        )

        self.assertTrue(self.waiting_system_state(SystemState.NAV_OFF_PATH))

    def test_move_rotate_shelf_angle_error(self):
        """收到移动任务，任务角度在约束下无法旋转货架"""
        self.adapter_admin.set_sros_pose(
            Pose(86.819, 151.419, 89.897),
            shelf_pose=Pose(86.819, 151.419, -0.4),
            shelf_id='T3003193',
        )
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        self.rcs.move_to_pose_with_shelf(
            HuaweiPoint(86820, 150420, 0),
            shelf_moving_policy=0,
            shelf_target_angle=0,
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            type_code=MSG_REQ_LINEAR_MOVE_AFTER_RAISE_SHELF,
        )

        self.waiting_system_state(SystemState.BUSY, 0.2)
        self.assertTrue(self.waiting_system_state(SystemState.SHELF_ANGLE_ERROR))

    def test_move_rotate_fixed_upload_shelf_angle_error(self):
        """收到移动任务，调整策略允许调整"""
        self.adapter_admin.set_sros_pose(
            Pose(252.201, 610.125, -89.324),
            shelf_pose=Pose(252.201, 610.125, -89.324),
            shelf_id='MJ000132',
        )
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        dst_point = HuaweiPoint(252192, 610126, 0)
        self.rcs.move_to_pose_with_shelf(
            dst_point,
            shelf_type=2,
            shelf_moving_policy=ShelfAnglePolicy.Ignore,
            shelf_target_angle=ShelfAnglePolicy.Ignore,
            adjust_type=AdjustType.SMALL_ANGLE_TO_SHELF_NO_ROTATE_EXECUTOR,
            type_code=MSG_REQ_LINEAR_MOVE_AFTER_RAISE_SHELF,
        )

        assert self.waiting_system_state(SystemState.BUSY)
        assert self.waiting_system_state(SystemState.IDLE)

        GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point()), '没有到达最终目标点'

    def test_replan_online_and_move_on_72_deg(self):
        """测试解抱闸恢复后，斜线路径上线，然后移动(WIP: 具体行为待定)"""
        self.adapter_admin.set_sros_pose(
            Pose(99.888, 53.948, 90.47),
            shelf_pose=Pose(99.888, 53.948, 89.7),
            shelf_id='T3003192',
        )
        time.sleep(0.4)  # 等待适配器和调度都更新车的位置

        dst_point1 = HuaweiPoint(99888, 53948, -72000)
        self.rcs.move_to_pose_with_shelf(
            dst_point1,
            shelf_moving_policy=0,
            shelf_target_angle=288000,
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            task_id=25929,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        _logger.debug('这个斜线移动后，小车自己把小车方向摆到 -90 度？')
        dst_point2 = HuaweiPoint(100114, 53235, -72000)
        self.rcs.move_to_pose_with_shelf(
            dst_point2,
            shelf_moving_policy=0,
            shelf_target_angle=288000,
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            task_id=25929,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        _logger.debug('重发6次，小车角度转回 -72')
        for _ in range(6):
            self.rcs.move_to_pose_with_shelf(
                dst_point2,
                shelf_moving_policy=0,
                shelf_target_angle=288000,
                adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
                task_id=25929,
            )
            time.sleep(0.5)

        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

        _logger.debug('再发一次，小车角度转回 -90，角度异常卡住')
        self.rcs.move_to_pose_with_shelf(
            HuaweiPoint(100114, 53235, -90000),
            shelf_moving_policy=0,
            shelf_target_angle=270000,
            adjust_type=AdjustType.NO_ROTATE_EXECUTOR,
            task_id=25929,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.SHELF_ANGLE_ERROR))


if __name__ == '__main__':
    unittest.main()
