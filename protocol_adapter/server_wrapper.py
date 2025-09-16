import logging
import threading
import socket

from protocol_adapter.utils import ThreadTask

_logger = logging.getLogger(__name__)

ALARM_RESEND_INTERVAL = 0.3
ALARM_RETRY = 2
BUFFER_SIZE = 1024


class ServerWrapper:
    def __init__(self, callback_receive_data, callback_receive_from_alarm_server):
        self._callback_receive_data = callback_receive_data
        self._callback_receive_from_alarm_data = callback_receive_from_alarm_server

        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._server = None
        self._alarm_server = None  # 告警服务器
        self._mutex_locker = threading.Lock()

        self._msg_sn = 1  # 消息sn
        self._alarm_sn = 1

        # 告警状态重发机制，记录最后一个告警数据，超时未收到应答则重发
        # TODO 由于告警应答数据无法区分对应的是哪个请求的告警，如果出现
        # 连续多个告警类型同时上报，如先发送急停告警，没有收到系统应答前
        # 出现电机故障告警并发送到服务器，服务器返回应答时无法区分是应答
        # 哪个告警，目前只考虑同一时刻只有一个告警上报的简单场景
        self._alarm_resend_dat = None
        self._alarm_resender = None

        self._is_running = False

    def start(self, local_port=0):
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if local_port > 0:
            _logger.info(f'bind local port: {local_port}')
            self._udp_socket.bind(('', local_port))

        # 1s 周期检查一次是否正在运行
        self._udp_socket.settimeout(1)

        self._is_running = True
        self.start_recv_dat()

    def stop(self):
        self._is_running = False

    def get_server(self):
        return self._server

    def set_server(self, server):
        ip, port = server
        _logger.info(f'set server: {ip} {port}')
        self._server = (ip, int(port))

    def set_alarm_server(self, server):
        _logger.info(f'set alarm server: {server}')
        self._alarm_server = server

    def get_msg_sn(self):
        return self._msg_sn

    def get_alarm_sn(self):
        return self._alarm_sn

    def start_recv_dat(self):
        t = threading.Thread(target=self.recv_data, name='cmd_receiver')
        t.start()
        _logger.info('Start receive thread')

    def send_request(self, dat, server=None):
        self._mutex_locker.acquire()
        self.send_data(dat, server)
        self._msg_sn += 1
        self._mutex_locker.release()

    def send_alarm(self, dat):
        self.do_send_alarm(dat)
        self._alarm_sn += 1

        # 默认发出数据会丢，除非真的收到回应
        self._alarm_resend_dat = dat

        def resend_alarm():
            _logger.info('alarm response timeout, resend ..')
            if self._alarm_resend_dat is None:
                return True
            self.do_send_alarm(self._alarm_resend_dat)
            return False

        if self._alarm_resender:
            self._alarm_resender.stop()

        self._alarm_resender = ThreadTask(
            on_retry=resend_alarm,
            retry_interval=ALARM_RESEND_INTERVAL,
            max_try=ALARM_RETRY,
            name='alarm_resender',
        )
        self._alarm_resender.start(delay=ALARM_RESEND_INTERVAL)

    def do_send_alarm(self, dat):
        if self._alarm_server is None:
            _logger.error('alarm server not set')
            return
        try:
            self._udp_socket.sendto(dat, self._alarm_server)
        except BaseException as e:
            _logger.info(f'alarm send exception: {e}')

    def send_data(self, dat, server=None):
        if server is None:
            server = self._server

        if server is None:
            _logger.error('server addr not set')
            return

        try:
            self._udp_socket.sendto(dat, server)
        except BaseException as e:
            _logger.info(f'Network exception: {e}')

    def recv_data(self):
        while self._is_running:
            try:
                recv_dat, addr_info = self._udp_socket.recvfrom(BUFFER_SIZE)
                if not recv_dat:
                    continue
                if self._alarm_server == addr_info:
                    self._callback_receive_from_alarm_data(recv_dat)
                    self._alarm_resend_dat = None
                    if self._alarm_resender:
                        self._alarm_resender.stop()
                else:
                    self._callback_receive_data(recv_dat)
            except socket.timeout:
                continue
            except BaseException as e:
                _logger.error(e, exc_info=True)

        # stop() 后会来到这里，重新启动需要 start()
        self._udp_socket.close()
