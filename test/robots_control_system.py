#!/usr/bin/python3
import copy
import logging
import socket
import threading

from protocol_adapter.utils import GeometryUtils
from protocol_adapter.models.state import SystemState
from protocol_adapter.models.task import TaskType, TaskItem
from protocol_adapter.huawei_protocol import HuaweiProtocol
from protocol_adapter.huawei_model.point import Point
from protocol_adapter.huawei_model import const
from protocol_adapter.huawei_model.const import (
    AdjustType,
    DetectType,
    ShelfAnglePolicy,
    ShelfType,
)
from protocol_adapter.huawei_model.roller_info import RollerInfo
from protocol_adapter.const import ActuatorIdx

from test.asyncio_protocol import AsyncioProtocol

_logger = logging.getLogger(__name__)


class Protocol:
    def __init__(self, asyncio_protocol):
        self.transport = None
        self._asyncio_protocol = asyncio_protocol

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self._asyncio_protocol.datagram_received(data, addr)

    def connection_lost(self, exc):
        _logger.info(f'Socket closed: {exc}')


class RobotsControlSystem(AsyncioProtocol):
    """
    模拟华为的RCS但是我们现在只支持一台车链接
    """

    _huawei_protocol: HuaweiProtocol

    def __init__(self, port=8988):
        super().__init__()
        self._server_ip = '0.0.0.0'
        self._server_port = port
        # 存储一些车辆相关的信息
        self._device_id = 0
        self._addr = None  # 车辆地址
        self._cur_point = Point()  # 车辆当前位置
        self.system_state = SystemState.NONE  # 车辆系统状态
        self.dmcode_type = ''  # 地图二维码类型（中间两字母）
        # 载货信息
        self.actuator_shelf_id_str = ''  # 车辆上传的货架ID
        self.shelf_angle = 0  # 车辆上传的货架角度
        self._dst_point = Point()  # 车辆的目标点
        self.roller_info = {}  # 滚筒载货信息
        self.smt_info = {}  # SMT工装信息
        self.dst_distance = 0  # 离目标点的距离
        self._allow_lock_space_default = True  # 默认是否允许旋转
        self._allow_lock_space_rule: dict = {}  # 锁空间规则{Point： [LOCK_SPACE_TYPE]}
        self._allow_unlock_space = True  # 是允许车辆释放空间
        self._client_registered = threading.Event()  # 客户端注册信号

    def start(self):
        self.bind_socket()
        super().start()

    def set_allow_lock_space_default(self, allow: bool):
        self._allow_lock_space_default = allow

    def set_allow_lock_space_rule(self, rule: dict):
        self._allow_lock_space_rule = rule

    def set_allow_unlock_space(self, allow: bool):
        self._allow_unlock_space = allow

    def get_cur_point(self):
        return copy.deepcopy(self._cur_point)

    def get_server_port(self) -> int:
        return self._server_port

    def bind_socket(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self._server_ip, self._server_port))

        _logger.info(f'RCS server listen on {self._server_ip}:{self._server_port}/udp')
        self._huawei_protocol = HuaweiProtocol()

    def wait_client_register(self):
        if not self._client_registered.is_set():
            _logger.warning('wait client register ..')
            self._client_registered.wait()

    async def _connect(self):
        self._transport, self._protocol = await self._loop.create_datagram_endpoint(
            lambda: Protocol(self), sock=self._sock
        )

    @AsyncioProtocol.run_coroutine_threadsafe
    async def pause_task(
        self,
        task_id=115,
        sub_task_id=114,
    ):
        dat = self._huawei_protocol.pack_pause_task(
            device_id=self._device_id, msg_sn=4, task_id=task_id, sub_task_id=sub_task_id
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def continue_task(
        self,
        task_id=113,
        sub_task_id=112,
    ):
        dat = self._huawei_protocol.pack_continue_task(
            device_id=self._device_id, msg_sn=4, task_id=task_id, sub_task_id=sub_task_id
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def stop_move(
        self,
        task_id=113,
        sub_task_id=112,
    ):
        dat = self._huawei_protocol.pack_stop_move_task(
            device_id=self._device_id, msg_sn=4, task_id=task_id, sub_task_id=sub_task_id
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def move_to_pose(
        self,
        point,
        task_type=TaskItem.Normal,
        task_id=1,
        sub_task_id=1,
        type_code=const.MSG_REQ_NO_PAYLOAD_LINEAR_MOVE,
        limit_v=1000,
        stop_distance=2000,
    ):
        self._dst_point = point
        dat = self._huawei_protocol.pack_no_payload_linear_move_req(
            msg_sn=4,
            x=point.x,
            y=point.y,
            angle=point.angle,
            type_code=type_code,
            device_id=self._device_id,
            task_type=task_type,
            task_id=task_id,
            sub_task_id=sub_task_id,
            limit_v=limit_v,
            stop_distance=stop_distance,
        )
        self._transport.sendto(dat, self._addr)

    def move_multi_paths_with_no_payload(
        self,
        point,
        points_groups,
        task_id=1,
        sub_task_id=1,
    ):
        self._dst_point = point
        dat = self._huawei_protocol.pack_multi_no_payload_move(
            msg_sn=4,
            x=point.x,
            y=point.y,
            angle=point.angle,
            type_code=const.MSG_REQ_LINEAR_NO_PAYLOAD_MULTI_PATH_MOVE,
            device_id=self._device_id,
            points_groups=points_groups,
            task_id=task_id,
            sub_task_id=sub_task_id,
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def raise_shelf_action(
        self,
        point,
        shelf_id_str: str,
        shelf_moving_policy=ShelfAnglePolicy.Ignore,
        shelf_target_angle=ShelfAnglePolicy.Ignore,
        adjust_type=AdjustType.NO_LIMIT,
        task_id=1,
        sub_task_id=1,
    ):
        self._dst_point = point
        dat = self._huawei_protocol.pack_execute_shelf_req(
            self._device_id,
            10,
            shelf_id_str=shelf_id_str,
            x=point.x,
            y=point.y,
            angle=point.angle,
            shelf_moving_policy=shelf_moving_policy,
            shelf_target_angle=shelf_target_angle,
            task_type=TaskItem.Shelf_Leg_Identify,
            type_code=const.MSG_REQ_RAISE_SHELF,
            adjust_type=adjust_type,
            task_id=task_id,
            sub_task_id=sub_task_id,
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def put_down_shelf_action(
        self,
        point,
        task_id=1,
        sub_task_id=1,
        adjust_type=AdjustType.NO_LIMIT,
    ):
        self._dst_point = point
        dat = self._huawei_protocol.pack_execute_shelf_req(
            self._device_id,
            10,
            x=point.x,
            y=point.y,
            angle=point.angle,
            shelf_moving_policy=ShelfAnglePolicy.Ignore,
            shelf_target_angle=ShelfAnglePolicy.Ignore,
            adjust_type=adjust_type,
            task_type=TaskItem.Shelf_Leg_Identify,
            type_code=const.MSG_REQ_PUT_SHELF,
            task_id=task_id,
            sub_task_id=sub_task_id,
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def put_down_shelf_and_move(
        self,
        point,
        task_id=1,
        sub_task_id=1,
        adjust_type=AdjustType.NO_LIMIT,
    ):
        self._dst_point = point
        dat = self._huawei_protocol.pack_execute_shelf_req(
            self._device_id,
            10,
            x=point.x,
            y=point.y,
            angle=point.angle,
            shelf_moving_policy=ShelfAnglePolicy.Ignore,
            shelf_target_angle=ShelfAnglePolicy.Ignore,
            adjust_type=adjust_type,
            task_type=TaskItem.Shelf_Leg_Identify,
            type_code=TaskType.Linear_Move_After_Put_Shelf,
            task_id=task_id,
            sub_task_id=sub_task_id,
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def move_to_pose_with_shelf(
        self,
        point,
        shelf_moving_policy=ShelfAnglePolicy.Ignore,
        shelf_target_angle=ShelfAnglePolicy.Ignore,
        type_code=TaskType.Linear_Move_After_Raise_Shelf,
        arc_points=None,
        points_groups=None,
        shelf_type=ShelfType.Rectangle,
        adjust_type=AdjustType.NO_LIMIT,
        task_id=1,
        sub_task_id=1,
    ):
        self._dst_point = point
        dat = self._huawei_protocol.pack_execute_shelf_req(
            self._device_id,
            10,
            x=point.x,
            y=point.y,
            angle=point.angle,
            shelf_moving_policy=shelf_moving_policy,
            shelf_target_angle=shelf_target_angle,
            shelf_type=shelf_type,
            task_type=TaskItem.Normal,
            type_code=type_code,
            arc_points=arc_points,
            points_groups=points_groups,
            adjust_type=adjust_type,
            task_id=task_id,
            sub_task_id=sub_task_id,
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def shelf_sn_detect(
        self, point: Point, continue_time, detect_type=DetectType.Default
    ) -> None:
        """探测货架ID
        任务类型ID: TaskType.Shelf_SN_Detect
        type_code: MSG_REQ_DETECT_CTRL
        param: x、y、angle   xy位置 angle角度
        """
        dat = self._huawei_protocol.pack_shelf_sn_detect_req(
            self._device_id, 3, point.x, point.y, point.angle, continue_time, detect_type
        )
        self._transport.sendto(dat, self._addr)

    def smt_control(
        self,
        dst_point,
        points_groups,
        smt_info,
        type_code,
        task_id=1,
        sub_task_id=1,
        move_with_action=0,
    ):
        dat = self._huawei_protocol.pack_execute_smt_req(
            self._device_id,
            msg_sn=10,
            x=dst_point.x,
            y=dst_point.y,
            angle=dst_point.angle,
            points_groups=points_groups,
            smt_ctrl_info=smt_info,
            type_code=type_code,
            task_id=task_id,
            sub_task_id=sub_task_id,
            move_with_action=move_with_action,
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def arc_move(self, point_dst: Point, point0: Point, point1: Point) -> None:
        dat = self._huawei_protocol.pack_arc_no_payload_move(
            self._device_id,
            10,
            point_dst.x,
            point_dst.y,
            point_dst.angle,
            [point0, point1],
            task_id=11,
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def change_map(self, dmcode_type: str, ip: str, port: int, point: Point) -> None:
        dat = self._huawei_protocol.pack_change_map_req(
            self._device_id, 10, dmcode_type, ip, port, point.x, point.y, point.angle
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def charge(self, point):
        self._dst_point = point
        dat = self._huawei_protocol.pack_charge_req(
            self._device_id, msg_sn=5, x=point.x, y=point.y, angle=point.angle
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def stop_charge(self, point):
        self._dst_point = point
        dat = self._huawei_protocol.pack_stop_charge_req(
            self._device_id, msg_sn=5, x=point.x, y=point.y, angle=point.angle
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def control_roller(
        self,
        point,
        roller0=RollerInfo(),
        roller1=RollerInfo(),
        roller2=RollerInfo(),
        roller3=RollerInfo(),
        task_id=1,
        sub_task_id=1,
    ):
        self._dst_point = point
        dat = self._huawei_protocol.pack_execute_roller_req(
            self._device_id,
            5,
            point.x,
            point.y,
            point.angle,
            roller0,
            roller1,
            roller2,
            roller3,
            task_id=task_id,
            sub_task_id=sub_task_id,
        )
        self._transport.sendto(dat, self._addr)

    @AsyncioProtocol.run_coroutine_threadsafe
    async def cancel_task(self):
        dat = self._huawei_protocol.pack_cancel_task(self._device_id, msg_sn=5)
        self._transport.sendto(dat, self._addr)

    def datagram_received(self, data, addr):
        msg_header = data[: const.MSG_HEADER_LEN]
        header = self._huawei_protocol.unpack_header(msg_header)
        sn = header['sn']
        msg_body = data[const.MSG_HEADER_LEN :]
        if len(msg_body) > 4:
            self._device_id = int.from_bytes(
                msg_body[0:4], byteorder=const.BYTES_ORDER, signed=False
            )
        else:
            self._device_id = 0
        type_code = header['type']
        if type_code == const.MSG_REQ_REGISTER:
            _logger.info('device request register')
            response = self._huawei_protocol.pack_register_resp(
                self._device_id, sn, const.RESPONSE_OKAY, 0
            )
            self._transport.sendto(response, addr)
            self._addr = addr
            self._client_registered.set()

            # 按协议说明，注册后下发配置
            self._send_config_to_client(addr)

        elif type_code == const.MSG_REQ_REPLAN_ONLINE:
            _logger.info('device request replan online')
            data = self._huawei_protocol.pack_common_rsp(
                self._device_id, 5, const.MSG_RSP_REPLAN_ONLINE
            )
            self._transport.sendto(data, addr)
        elif type_code == const.MSG_REQ_UPLOAD_STATE:
            response = self._huawei_protocol.pack_status_upload_rsp(
                self._device_id, sn, const.RESPONSE_OKAY, 0
            )
            self._transport.sendto(response, addr)

            result = self._huawei_protocol.unpack_upload_status_req(msg_body)
            self._cur_point = result['point']
            self.dmcode_type = result['dmcode_type']
            self.system_state = SystemState(result['system_state'])
            self._update_dst_distance()
            if result['actuator_idx'] in (ActuatorIdx.SHELF, ActuatorIdx.GOODS):
                self.actuator_shelf_id_str = result['actuator_info']['shelf_id']
                self.shelf_angle = result['actuator_info']['shelf_angle']
            elif result['actuator_idx'] == ActuatorIdx.ROLLER:
                self.roller_info = result['actuator_info']
            elif result['actuator_idx'] == ActuatorIdx.SMT:
                self.smt_info = result['actuator_info']
        elif type_code == const.MSG_REQ_UPLOAD_ABILITY:
            linear_acc = int.from_bytes(msg_body[12:16], byteorder=const.BYTES_ORDER, signed=True)
            _logger.info('get upload device ability: ' + str(linear_acc))
            data = self._huawei_protocol.pack_common_rsp(
                self._device_id,
                sn,
                const.MSG_RSP_UPLOAD_ABILITY,
                const.RESPONSE_OKAY,
            )
            self._transport.sendto(data, addr)
        elif type_code == const.MSG_REQ_LOCK_SPACE:
            result = self._huawei_protocol.unpack_lock_space_req(msg_body)
            _logger.debug(
                f'request lockspace {result["lock_type"]} at ({result["cur_x"]}, {result["cur_y"]})'
            )
            allow_lock_space = self._allow_lock_space_default
            for point, allow_lock_type in self._allow_lock_space_rule.items():
                if abs(point.x - result['cur_x']) <= 100 and abs(point.y - result['cur_y']) <= 100:
                    if result['lock_type'] in allow_lock_type:
                        allow_lock_space = True
                    else:
                        _logger.warning(f'{point}处只允许申请{allow_lock_type}')
                    break
            else:
                _logger.debug(
                    f'({result["cur_x"]}, {result["cur_y"]})处未设置是否允许旋转，'
                    f'使用默认值{self._allow_lock_space_default}'
                )
            response = self._huawei_protocol.pack_lock_space_rsp(
                self._device_id,
                sn,
                const.MSG_RSP_LOCK_SPACE,
                result=1 if allow_lock_space else 0,
                err_code=17,
            )
            self._transport.sendto(response, addr)
        elif type_code == const.MSG_REQ_UNLOCK_SPACE:
            response = self._huawei_protocol.pack_lock_space_rsp(
                self._device_id,
                sn,
                const.MSG_RSP_UNLOCK_SPACE,
                result=1 if self._allow_unlock_space else 0,
            )
            self._transport.sendto(response, addr)
        elif type_code == const.MSG_RSP_NO_PAYLOAD_LINEAR_MOVE:
            rsp = int.from_bytes(msg_body[4:8], byteorder=const.BYTES_ORDER, signed=True)
            _logger.info('no payload move rsp: ' + str(rsp))
        elif type_code == const.MSG_RSP_RAISE_SHELF:  # 举升指令执行成功响应数据
            _logger.info('get raise shelf response')
        elif type_code == const.MSG_RSP_PUT_SHELF:  # 放下货架指令执行成功响应数据
            _logger.info('get put shelf response')
        elif type_code == const.MSG_RSP_DETECT_CTRL:  # 探测货架指令执行成功响应数据
            _logger.info('get shelf detect ctrl')
        elif type_code == const.MSG_RSP_CHANGE_MAP:
            _logger.debug('change map response')
        elif type_code == const.MSG_REQ_NOTIFY_MAP_CHANGE:
            _logger.debug('map changed notification')
            response = self._huawei_protocol.pack_common_rsp(
                self._device_id, sn, const.MSG_RSP_NOTIFY_MAP_CHANGE
            )
            self._transport.sendto(response, addr)
        elif type_code == const.MSG_REQ_ROLLER_CTRL:
            response = self._huawei_protocol.pack_common_rsp(
                self._device_id,
                sn,
                const.MSG_RSP_ROLLER_CTRL,
                result=const.RESPONSE_OKAY,
                err_code=None,
            )
            self._transport.sendto(response, addr)

        elif type_code == const.MSG_REQ_CANCEL:
            response = self._huawei_protocol.pack_common_rsp(
                self._device_id,
                sn,
                const.MSG_RSP_CANCEL,
                result=const.RESPONSE_OKAY,
                err_code=None,
            )
            self._transport.sendto(response, addr)

        else:
            rsp = int.from_bytes(msg_body[4:8], byteorder=const.BYTES_ORDER, signed=True)

    def _send_config_to_client(self, addr):
        # status config
        data = self._huawei_protocol.pack_cfg_upload_status_req(device_id=self._device_id, msg_sn=5)
        self._transport.sendto(data, addr)

        # warning server config
        data = self._huawei_protocol.pack_cfg_warning_server_req(
            device_id=self._device_id, msg_sn=5
        )
        self._transport.sendto(data, addr)

    def _update_dst_distance(self):
        """计算与目标点的距离"""
        self.dst_distance = GeometryUtils.calculate_distance(
            self._cur_point.x, self._cur_point.y, self._dst_point.x, self._dst_point.y
        )


if __name__ == '__main__':
    from protocol_adapter.utils import SrosLog

    sros_log = SrosLog('rcs_mock')
    sros_log.sendLogToConsole()

    server = RobotsControlSystem()
    server.start()
