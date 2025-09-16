# Copyright 2024 Standard Robots Co. All rights reserved.
import time
import unittest
import logging

from protocol_adapter.models.state import SystemState
from protocol_adapter.huawei_model.const import (
    ROLLER_ACTION_PUT,
    ROLLER_ACTION_FETCH,
    ROLLER_DIR_RIGHT_OR_BEHIND,
)
from protocol_adapter.mock.world_mock import WorldMock
from protocol_adapter.huawei_model.roller_info import RollerInfo
from protocol_adapter.adapter_admin import AdapterAdmin
from protocol_adapter.const import DeviceType

from test.robots_control_system import RobotsControlSystem
from test.alarm_server import AlarmServer

_logger = logging.getLogger(__name__)


class RollerTest(unittest.TestCase):
    """辊筒车型相关的测试"""

    def setUp(self):
        self.alarm_server = AlarmServer()
        self.rcs = RobotsControlSystem()
        self.rcs.start()
        self.adapter_admin = AdapterAdmin(mock=True, device_type=DeviceType.ROLLER)
        self.adapter_admin.run()
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))

    def tearDown(self):
        self.rcs.stop()
        self.alarm_server.stop()
        self.adapter_admin.stop()
        WorldMock().reset()
        time.sleep(0.2)  # 等待端口关闭

    def waiting_system_state(self, state, time_out_s=60) -> bool:
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

    def test_pick_and_drop(self):
        """测试辊筒取放货。
        模拟华为团泊洼D区终端的辊筒，单辊筒，辊筒滚动方向和车平行，只有车尾方向可以进出货物"""
        point = self.rcs.get_cur_point()
        # 取货
        self.rcs.control_roller(
            point,
            roller0=RollerInfo(ROLLER_ACTION_FETCH, ROLLER_DIR_RIGHT_OR_BEHIND, 1),
            task_id=1,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertEqual(self.rcs.roller_info.get('roller0', 0), 1, '取货失败')
        time.sleep(2.1)  # 连续发任务中间要等，见：ExecuteTask.start()
        # 放货
        self.rcs.control_roller(
            point,
            roller0=RollerInfo(ROLLER_ACTION_PUT, ROLLER_DIR_RIGHT_OR_BEHIND, 1),
            task_id=2,
        )
        self.assertTrue(self.waiting_system_state(SystemState.BUSY))
        self.assertTrue(self.waiting_system_state(SystemState.IDLE))
        self.assertEqual(self.rcs.roller_info.get('roller0', 0), 0, '放货失败')


if __name__ == '__main__':
    unittest.main()
