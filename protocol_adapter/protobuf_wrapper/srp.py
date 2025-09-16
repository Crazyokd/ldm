import asyncio
import logging
import threading
import socket

from protocol_adapter.huawei_model.smt_info import SmtState
from protocol_adapter.protobuf_wrapper import main_pb2
from protocol_adapter.protobuf_wrapper import srp_protobuf
from protocol_adapter.protobuf_wrapper.async_result import AsyncResult

_logger = logging.getLogger(__name__)


class SrpProtocol(asyncio.Protocol):
    def __init__(self, srp):
        self._srp = srp

    def connection_made(self, transport):
        self._srp.connection_made(transport)

    def data_received(self, data):
        self._srp.data_received(data)

    def error_received(self, exc):
        self._srp.error_received(exc)

    def connection_lost(self, exc):
        self._srp.connection_lost(exc)


class SRP:
    """
    @describe:  本类用来和sros通信
                本类内部有一个线程用于处理protobuf协议的解析、收发，本类是线程安全的
                本类的方法既支持同步通信的方式也支持异步通信的方式，同步通信的方式主要用来测试，比如连续发送task而不等回复
                默认为异步函数，同步函数前面都加了前缀:sync_,和node.js的库命名规范类似
    @NOTE: 异步调用时，假定不会同时调用， 现在只有一个AsyncResult类来阻塞等待sros的响应
    """

    _loop: asyncio.AbstractEventLoop
    _sync_result: AsyncResult
    _sync_task_result: AsyncResult  # 同步等待任务（动作）执行结束
    _location_result: AsyncResult  # 取消定位、定位同步结果
    _transport: asyncio.Transport
    _protocol: SrpProtocol

    def __init__(self):
        self._protobuf = srp_protobuf.SrpProtobuf(self.write_callback, self.response_callback)
        self._protobuf.set_system_state_callback(self.on_system_state)
        self._protobuf.set_notify_move_task_finished_callback(self.on_move_task_finish)
        self._protobuf.set_notify_action_task_finished_callback(self.on_action_task_finish)
        self._seq = 0
        self._wait_seq = 0  # 等待回复的seq

        self._last_location_state = main_pb2.SystemState.LocationState.LOCATION_STATE_ZERO

        self._callback_system_state = None
        self._callback_connect_changed = None
        self._callback_move_task_finish = None
        self._callback_action_task_finish = None

        loop_ready = threading.Event()

        def start_loop():
            # create loop in the new thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            # rely on the thread event loop to be set
            self._sync_result = AsyncResult(self._loop)
            self._sync_task_result = AsyncResult(self._loop)
            self._location_result = AsyncResult(self._loop)

            loop_ready.set()

            try:
                self._loop.run_forever()
            finally:
                for task in asyncio.all_tasks(self._loop):
                    task.cancel()
                self._loop.run_until_complete(self._loop.shutdown_asyncgens())
                self._loop.close()

        self._thread = threading.Thread(target=start_loop, name='srp')
        self._thread.start()

        loop_ready.wait()

    def stop(self):
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()

    def set_callback_connect(self, fun):
        self._callback_connect_changed = fun

    def set_system_state_callback(self, fun):
        self._callback_system_state = fun

    def set_hardware_state_callback(self, fun):
        self._protobuf.set_hardware_state_callback(fun)

    def set_sensor_samples_callback(self, fun):
        self._protobuf.set_sensor_samples_callback(fun)

    def set_laser_point_callback(self, fun):
        self._protobuf.set_laser_point_callback(fun)

    def set_notify_move_task_finished_callback(self, fun):
        self._callback_move_task_finish = fun

    def set_notify_action_task_finished_callback(self, fun):
        self._callback_action_task_finish = fun

    def set_notify_mission_list_change_callback(self, fun):
        self._protobuf.set_notify_mission_list_change_callback(fun)

    def on_system_state(self, sys_state):
        if self._callback_system_state:
            self._callback_system_state(sys_state)

    def on_move_task_finish(self, notification):
        if self._callback_move_task_finish:
            self._callback_move_task_finish(notification.movement_task)

    def on_action_task_finish(self, notification):
        # 不用判断wait_seq，因为在执行动作后可能进行了其他操作
        action_task = notification.action_task
        self._sync_task_result.accept(action_task)
        if self._callback_action_task_finish:
            self._callback_action_task_finish(action_task)

    def set_location_result(self, result):
        _logger.info(f'Set location result: {result}')
        if result:
            self._location_result.accept(result)
        else:
            self._location_result.reject(result)

    def login(self, ip_addr, user_name, passwd) -> bool:
        """
        登录sros
        :param ip_addr: target sros's ip address
        :param user_name: clear text
        :param passwd: clear text
        :return: none
        """
        try:
            f = asyncio.run_coroutine_threadsafe(self._connect(ip_addr), self._loop)
            result = f.result(3)
            if not result:
                return False
            _logger.info(f'Connect succeed: {ip_addr}:5001')
        except BaseException as e:
            _logger.error(f'srp connect exception: {e}')
            return False

        try:
            self._run_sync_threadsafe(self._protobuf.login, user_name, passwd)
            if self._callback_connect_changed:
                self._callback_connect_changed(True)
            return True
        except BaseException as e:
            _logger.error(f'Login sros failed: {e}')
        return False

    def logout(self):
        try:
            self._run_sync_threadsafe(self._protobuf.logout)
        except BaseException as e:
            _logger.error(e)

        if self._transport:
            self._transport.close()

        if self._callback_connect_changed:
            self._callback_connect_changed(False)

    def fetch_system_state(self):
        return self._run_sync_threadsafe(self._protobuf.get_system_state)

    def fetch_hardware_state(self):
        return self._run_sync_threadsafe(self._protobuf.get_hardware_state)

    def fetch_sensor_samples(self):
        return self._run_sync_threadsafe(self._protobuf.get_sensor_samples)

    def get_smt_state(self):
        state = SmtState()
        unit = state.units[0]

        STATE_REG_ADDR = 30330
        STATE_REG_SIZE = 10

        # c++ 里读取 int16 的数字, 转换成 uint16_t 通过 protobuf 存储成 int32 后传输
        def restore_int16(value):
            uint16_value = value & 0xFFFF
            # 如果 uint16_value >= 32768，说明原始是负数（补码表示）
            if uint16_value >= 0x8000:
                return uint16_value - 0x10000
            else:
                return uint16_value

        registers = self._run_sync_threadsafe(
            self._protobuf.readInputRegisters, STATE_REG_ADDR, STATE_REG_SIZE, timeout=0.2
        )
        if registers and len(registers) == STATE_REG_SIZE:
            unit.action_type = restore_int16(registers[0])
            unit.action_direction = restore_int16(registers[1])
            unit.lift_height = restore_int16(registers[2])
            unit.lift_speed = restore_int16(registers[3])
            unit.adjust_width = restore_int16(registers[4])
            unit.adjust_width_speed = restore_int16(registers[5])
            unit.docking_state = restore_int16(registers[6])
            unit.cargo_state = restore_int16(registers[7])
            unit.cargo_type = restore_int16(registers[8])
        else:
            _logger.error('invalid read of smt state registers')

        # TODO(zZ): 打印 smt 工装状态
        import time

        if int(time.time() * 10) % 20 == 0:
            _logger.info(f'smt_state: {state}')

        return state

    def get_sros_config(self, key):
        configs = self._run_sync_threadsafe(self._protobuf.get_sros_config)
        for config in configs:
            if config.key == key:
                return config.value
        return None

    # TODO 没有考虑配置参数没有找到的情况
    def get_sros_configs(self, keys: list) -> dict:
        configs = self._run_sync_threadsafe(self._protobuf.get_sros_config)
        result = {}
        for config in configs:
            for key in keys:
                if config.key == key:
                    result[key] = config.value
        return result

    def set_sros_cache_configs(self, configs):
        self._run_sync_threadsafe(self._protobuf.set_sros_cache_configs, configs)

    def get_info(self):
        info = self._run_sync_threadsafe(self._protobuf.get_info)
        return info

    def triger_emergency(self):
        self._run_sync_threadsafe(self._protobuf.setEmergency)

    def cancel_emergency(self):
        self._run_sync_threadsafe(self._protobuf.cancelEmergencyState)

    def move_to_station(
        self, no, station_id, avoid_policy=main_pb2.MovementTask.OBSTACLE_AVOID_WAIT
    ):
        self._run_sync_threadsafe(self._protobuf.move_to_station, no, station_id, avoid_policy)

    def move_follow_path(
        self,
        no,
        paths,
        cancel_task_decetect_dmcode,
        avoid_policy=main_pb2.MovementTask.OBSTACLE_AVOID_WAIT,
    ):
        self._run_sync_threadsafe(
            self._protobuf.move_follow_path, no, paths, cancel_task_decetect_dmcode, avoid_policy
        )

    # 追加路径
    def replace_move_path(self, no, paths, cancel_task_decetect_dmcode):
        self._run_sync_threadsafe(
            self._protobuf.replace_move_path, no, paths, cancel_task_decetect_dmcode
        )

    def pause_task(self):
        self._run_sync_threadsafe(self._protobuf.pause_task)

    def continue_task(self):
        self._run_sync_threadsafe(self._protobuf.continue_task)

    def cancel_task(self):
        self._run_sync_threadsafe(self._protobuf.cancel_task)

    def cancel_movement_task(self, soft_cancel):
        self._run_sync_threadsafe(self._protobuf.cancel_movement_task, soft_cancel)

    def set_manual_control(self, is_manual: bool):
        if is_manual:
            self._run_sync_threadsafe(self._protobuf.enable_manual_control)
        else:
            self._run_sync_threadsafe(self._protobuf.disable_manual_control)

    def set_traffic_control(self, enable: bool):
        if enable:
            self._run_sync_threadsafe(self._protobuf.enable_traffic_control)
        else:
            self._run_sync_threadsafe(self._protobuf.disable_traffic_control)

    def stop_location(self):
        self._run_sync_threadsafe(self._protobuf.stop_location)

    def set_current_map(self, map_name):
        self._run_sync_threadsafe(self._protobuf.set_current_map, map_name)

    def start_location(
        self, map_name, x, y, angle, x_factor, y_factor, absolute_location=False, timeout=60
    ):
        try:
            return self.switch_map(map_name, x, y, angle, absolute_location, timeout)
        except BaseException as e:
            _logger.error(e)

    def switch_map(self, map_name, x, y, angle, absolute_location=False, timeout=60):
        return self._run_sync_location_threadsafe(
            self._protobuf.switch_map, map_name, x, y, angle, absolute_location, timeout=timeout
        )

    def start_charge(self, seq):
        self._protobuf.start_charge(seq)
        # self.async_execute_action_task(no, 78, 1, 0)
        _logger.info(f'async_execute_action_task Start charge is successful seq: {seq}')

    def stop_charge(self, seq):
        self._protobuf.stop_charge(seq)
        # self.async_execute_action_task(no, 78, 2, 0)
        _logger.info('async_execute_action_task Stop charge is successful')

    # 同步执行，直到动作结果返回或超时
    def execute_action_task(self, no, action_id, param0, param1, paramStr=''):
        _logger.info(f'Execute action {no} {action_id} {param0} {param1} {paramStr}')
        result = self._run_sync_task_threadsafe(
            self._protobuf.execute_action_task, no, action_id, param0, param1, paramStr
        )
        return result

    def cancel_action_task(self):
        self._run_sync_threadsafe(self._protobuf.cancel_action_task)

    def read_input_registers(self, start_addr, count):
        return self._run_sync_threadsafe(self._protobuf.readInputRegisters, start_addr, count)

    # 以下为异步步指令
    def async_move_to_station(
        self, no, station_id, avoid_policy=main_pb2.MovementTask.OBSTACLE_AVOID_WAIT
    ):
        self._run_async_threadsafe(self._protobuf.move_to_station, no, station_id, avoid_policy)

    def async_execute_action_task(self, no, action_id, param0, param1):
        self._run_async_threadsafe(
            self._protobuf.execute_action_task, no, action_id, param0, param1
        )

    def _run_sync_threadsafe(self, fun, *args, timeout: float = 3):
        f = asyncio.run_coroutine_threadsafe(self._sync_request(fun, *args), self._loop)
        return f.result(timeout)

    # 移动动作任务同步执行直到返回结果
    def _run_sync_task_threadsafe(self, fun, *args, timeout=10 * 60):
        f = asyncio.run_coroutine_threadsafe(self._sync_task(fun, *args), self._loop)
        return f.result(timeout)

    def _run_sync_location_threadsafe(self, fun, *args, timeout=60):
        f = asyncio.run_coroutine_threadsafe(self._sync_location_task(fun, *args), self._loop)
        return f.result(timeout)

    async def _sync_request(self, fun, *args):
        self._seq += 1
        self._wait_seq = self._seq
        self._sync_result.clear()
        fun(self._seq, *args)
        return await self._sync_result.wait()

    async def _sync_task(self, fun, *args):
        self._seq += 1
        self._wait_seq = self._seq
        self._sync_task_result.clear()
        fun(self._seq, *args)
        return await self._sync_task_result.wait()

    # 定位任务，包括取消定位和重定位
    async def _sync_location_task(self, fun, *args):
        self._seq += 1
        self._wait_seq = self._seq
        self._location_result.clear()
        fun(self._seq, *args)
        return await self._location_result.wait()

    def _run_async_threadsafe(self, fun, *args):
        self._loop.call_soon_threadsafe(self._async_request, fun, *args)

    def _async_request(self, fun, *args):
        self._seq += 1
        fun(self._seq, *args)

    async def _connect(self, ip_addr):
        """
        由于同样的ip和port链接sros经常出问题，所以此处一直用端口号为8888的端口号链接sros
        :param ip_addr:
        :return:
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            SOURCE_PORT = 8888
            sock.bind(('0.0.0.0', SOURCE_PORT))
            sock.connect((ip_addr, 5001))
            self._transport, self._protocol = await self._loop.create_connection(
                lambda: SrpProtocol(self), sock=sock
            )
            return True
        except BaseException as e:
            _logger.error(f'Connect to sros failed: {e}')
        return False

    def connection_made(self, transport):
        _logger.info('connected!')

    def data_received(self, data):
        self._protobuf.onRead(data)

    def error_received(self, exc):
        _logger.error(f'Error received: {exc}')

    def connection_lost(self, exc):
        _logger.warning(f'Socket closed: {exc}')
        self.logout()

    def write_callback(self, data):
        self._transport.write(data)

    def response_callback(self, seq, response_type, ok, value=None, result_code=None):
        if seq == self._wait_seq:
            if ok:
                self._sync_result.accept(value)
            else:
                self._sync_result.reject(result_code)
                # 动作执行失败，需要抛出异常
                if response_type == main_pb2.Response.RESPONSE_COMMAND:
                    self._sync_task_result.reject(result_code)

    def get_result_code(self):
        return self._sync_result.get_result()
