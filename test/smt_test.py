#!/usr/bin/python3

import time
import logging
import pytest

from protocol_adapter.adapter_admin import AdapterAdmin
from protocol_adapter.const import DeviceType
from protocol_adapter.huawei_model.smt_info import SmtInfo
from protocol_adapter.mock.world_mock import WorldMock
from protocol_adapter.models.task import TaskType
from protocol_adapter.protobuf_wrapper.base import Pose
from protocol_adapter.utils.geometry import GeometryUtils
from test.alarm_server import AlarmServer
from test.robots_control_system import RobotsControlSystem
from protocol_adapter.models.state import SystemState
from protocol_adapter.huawei_model.point import Point as HuaweiPoint, SimplePoint


_logger = logging.getLogger(__name__)


class TestSmtCar:
    rcs: RobotsControlSystem

    @pytest.fixture(scope='function', autouse=True)
    def up_and_down(self):
        # 启动服务端
        alarm_server = AlarmServer()
        self.rcs = RobotsControlSystem()
        self.rcs.start()

        self.adapter_admin = AdapterAdmin(mock=True, device_type=DeviceType.SMT)
        self.adapter_admin.run()

        # 等待小车注册
        self.rcs.wait_client_register()

        # 执行测试用例
        yield

        # 停止相关线程
        self.adapter_admin.stop()
        alarm_server.stop()
        self.rcs.stop()
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

    def test_basic_move(self):
        """空车移动"""
        init_pose = Pose(110.295, 104.175, -90.871)
        self.adapter_admin.set_sros_pose(init_pose)
        time.sleep(0.3)  # 等待适配器和调度都更新车的位置

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

        # 目标点位姿 (X_mm, Y_mm, Yaw_mdeg)
        dst_point = HuaweiPoint(111760, 103821, 0)

        self.rcs.smt_control(
            dst_point,
            paths,
            smt_info=SmtInfo(),
            type_code=TaskType.Multi_Path_No_Payload_Move,
            task_id=1,
            sub_task_id=2,
        )

        assert self.waiting_system_state(SystemState.BUSY)
        assert self.waiting_system_state(SystemState.IDLE)

    def test_move_load_move_unload(self):
        """测试移动载货移动卸货"""

        init_pose = Pose(1, 2.2, 90.482)
        self.adapter_admin.set_sros_pose(init_pose)
        time.sleep(0.3)  # 等待适配器和调度都更新车的位置

        paths = [
            [
                SimplePoint(1000, 2200, 0, 600),
                SimplePoint(1000, 4000, 0, 600),
            ],
            [
                SimplePoint(1000, 4000, 0, 600),
                SimplePoint(2000, 4000, 0, 600),
            ],
        ]

        dst_point = HuaweiPoint(2000, 4000, 0)

        smt_info = SmtInfo()

        _logger.debug('第一次发空车移动任务')
        self.rcs.smt_control(
            dst_point,
            paths,
            smt_info=smt_info,
            type_code=TaskType.Multi_Path_No_Payload_Move,
            task_id=1,
            sub_task_id=2,
        )

        self.waiting_system_state(SystemState.BUSY, 0.3)
        time.sleep(1)

        _logger.debug('第二次发空车移动任务，移动中调高')
        smt_info.units[0].lift_height = 500
        smt_info.units[0].lift_speed = 400

        self.rcs.smt_control(
            dst_point,
            paths,
            smt_info=smt_info,
            type_code=TaskType.Multi_Path_No_Payload_Move,
            task_id=1,
            sub_task_id=2,
            move_with_action=1,
        )

        self.waiting_system_state(SystemState.BUSY, 0.3)
        assert self.waiting_system_state(SystemState.IDLE)
        assert GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point())

        _logger.debug('移动到位后载货')
        self.rcs.smt_control(
            dst_point,
            paths,
            smt_info=smt_info,
            type_code=TaskType.Smt_Load_Action,
            task_id=1,
            sub_task_id=3,
            move_with_action=1,
        )

        self.waiting_system_state(SystemState.BUSY, 0.3)
        assert self.waiting_system_state(SystemState.IDLE)

        _logger.debug('载货后移动')
        paths = [
            [
                SimplePoint(2000, 4000, 0, 600),
                SimplePoint(1200, 4000, 0, 600),
            ],
        ]
        dst_point = HuaweiPoint(1200, 4000, 180000)

        self.rcs.smt_control(
            dst_point,
            paths,
            smt_info=smt_info,
            type_code=TaskType.Smt_Multi_Path_Move,
            task_id=1,
            sub_task_id=4,
            move_with_action=1,
        )

        self.waiting_system_state(SystemState.BUSY, 0.3)
        assert self.waiting_system_state(SystemState.IDLE)
        assert GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point())

        _logger.debug('卸货')
        self.rcs.smt_control(
            dst_point,
            paths,
            smt_info=smt_info,
            type_code=TaskType.Smt_Unload_Action,
            task_id=1,
            sub_task_id=5,
            move_with_action=1,
        )

        self.waiting_system_state(SystemState.BUSY, 0.4)
        assert self.waiting_system_state(SystemState.IDLE)

    def test_move_direction(self):
        """测试全向移动方向"""

        init_pose = Pose(110.295, 104.175, -90.871)
        self.adapter_admin.set_sros_pose(init_pose)
        time.sleep(0.3)  # 等待适配器和调度都更新车的位置

        dst_point = HuaweiPoint(108295, 104110, -90000)
        self.rcs.move_to_pose(dst_point)

        assert self.waiting_system_state(SystemState.BUSY)
        assert self.waiting_system_state(SystemState.IDLE)

        assert GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point())

        # 路径组座标点 (X_mm, Y_mm, path_type, path_limit_v)
        paths = [
            [
                SimplePoint(108295, 104175, 0, 500),
                SimplePoint(110295, 103428, 0, 500),
            ],
            [
                SimplePoint(110295, 103428, 0, 500),
                SimplePoint(112295, 103428, 0, 500),
            ],
        ]

        # 目标点位姿 (X_mm, Y_mm, Yaw_mdeg)
        dst_point = HuaweiPoint(112295, 103428, 90000)

        self.rcs.smt_control(
            dst_point,
            paths,
            smt_info=SmtInfo(),
            type_code=TaskType.Multi_Path_No_Payload_Move,
            task_id=1,
            sub_task_id=2,
        )

        assert self.waiting_system_state(SystemState.BUSY)
        assert self.waiting_system_state(SystemState.IDLE)

        assert GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point())

    def test_move_direction_for_fit_near_path(self):
        """测试全向移动方向，全向移动排除自适应最近路径"""

        init_pose = Pose(61.344, 37.500, 179.966)
        self.adapter_admin.set_sros_pose(init_pose)
        time.sleep(0.3)  # 等待适配器和调度都更新车的位置

        # 目标点位姿 (X_mm, Y_mm, Yaw_mdeg)
        dst_point = HuaweiPoint(61280, 38200, 0)

        # 路径组座标点 (X_mm, Y_mm, path_type, path_limit_v)
        paths = [
            [
                SimplePoint(61280, 37500, 0, 500),
                SimplePoint(61280, 38200, 0, 500),
            ],
        ]

        self.rcs.smt_control(
            dst_point,
            paths,
            smt_info=SmtInfo(),
            type_code=TaskType.Multi_Path_No_Payload_Move,
            task_id=1,
            sub_task_id=2,
        )

        assert self.waiting_system_state(SystemState.BUSY)
        assert self.waiting_system_state(SystemState.IDLE)

        assert GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point())

    def test_move_direction_line_and_bezier(self):
        """测试全向移动方向，直线后接贝塞尔"""

        init_pose = Pose(94.374, 37.500, 179.966)
        self.adapter_admin.set_sros_pose(init_pose)
        time.sleep(0.3)  # 等待适配器和调度都更新车的位置

        # 路径组座标点 (X_mm, Y_mm, path_type, path_limit_v)
        paths = [
            [
                SimplePoint(91280, 37500, 0, 500),
                SimplePoint(96190, 37500, 0, 500),
            ],
            [
                SimplePoint(96190, 37500, 1, 500),
                SimplePoint(96960, 37500, 1, 500),
                SimplePoint(97730, 37500, 1, 500),
                SimplePoint(99270, 37500, 1, 500),
                SimplePoint(99270, 38295, 1, 500),
                SimplePoint(99270, 39090, 1, 500),
            ],
        ]

        # 目标点位姿 (X_mm, Y_mm, Yaw_mdeg)
        dst_point = HuaweiPoint(99270, 39090, 270000)

        self.rcs.smt_control(
            dst_point,
            paths,
            smt_info=SmtInfo(),
            type_code=TaskType.Multi_Path_No_Payload_Move,
            task_id=1,
            sub_task_id=2,
        )

        assert self.waiting_system_state(SystemState.BUSY)
        assert self.waiting_system_state(SystemState.IDLE)

        assert GeometryUtils.is_same_point(dst_point, self.rcs.get_cur_point())
