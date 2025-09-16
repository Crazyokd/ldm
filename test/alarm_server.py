#!/usr/bin/python3
import socket
import time

from protocol_adapter.loop_timer import Timer
from protocol_adapter.huawei_protocol import HuaweiProtocol
from protocol_adapter.huawei_model.const import (
    ALARM_HEADER_LEN,
    ALARM_CATEGORY_1,
    ALARM_CODE_LOST_CONNECT,
    ALARM_STATUS_OFF,
    ALARM_STATUS_ON,
)
import logging

_logger = logging.getLogger(__name__)


class AlarmServer:
    """注意这个也只支持一台车"""

    def __init__(self):
        self._udp_socket = None
        self._huawei_protocol = None
        self.is_running = True
        self._start_timer = Timer(1, self._run, name='AlarmServer')
        self._start_timer.start()
        self.is_robot_lost_connection = False

    def _run(self):
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._udp_socket.bind(('127.0.0.1', 8788))
        self._huawei_protocol = HuaweiProtocol()

        # 1s 周期检查一次是否正在运行
        self._udp_socket.settimeout(1)

        _logger.info('udp alarm server start')
        while self.is_running:
            try:
                dat, addr = self._udp_socket.recvfrom(1024)
            except socket.timeout:
                continue

            if addr is None:
                continue
            msg_header = dat[:ALARM_HEADER_LEN]
            header = self._huawei_protocol.unpack_alarm_header(msg_header)
            msg_body = dat[ALARM_HEADER_LEN:]
            alarm_body = self._huawei_protocol.unpack_alarm_request(msg_body)
            _logger.info(f'server receive alarm: {header} - {alarm_body}')

            if (
                alarm_body.category == ALARM_CATEGORY_1
                and alarm_body.type_code == ALARM_CODE_LOST_CONNECT
            ):
                if alarm_body.status == ALARM_STATUS_ON:
                    self.is_robot_lost_connection = True
                elif alarm_body.status == ALARM_STATUS_OFF:
                    self.is_robot_lost_connection = False

            rsp = self._huawei_protocol.pack_alarm_response(header.sn)
            self._udp_socket.sendto(rsp, addr)

        self._udp_socket.close()

    def stop(self):
        self.is_running = False


if __name__ == '__main__':
    alarm_server = AlarmServer()
    time.sleep(3)
    alarm_server.stop()
