# Copyright 2024 Standard Robots Co. All rights reserved.
import time
import json
import logging
from collections import namedtuple
from socket import inet_aton, inet_pton, inet_ntop, AF_INET6, AF_INET

from protocol_adapter.utils import AngleUtils, MiscUtils
from protocol_adapter.const import ActuatorIdx, DeviceType, NavigationMode
from protocol_adapter.models.task import TaskType, TaskItem
from protocol_adapter.huawei_model.linear_move_task import LinearMoveTask
from protocol_adapter.huawei_model.arc_move_task import ArcMoveTask
from protocol_adapter.huawei_model.multi_move_task import MultiMoveTask
from protocol_adapter.huawei_model.commad_task import CommandTask
from protocol_adapter.huawei_model.smt_info import SmtInfo, SmtState
from protocol_adapter.huawei_model.point import Point
from protocol_adapter.huawei_model.const import *
from protocol_adapter.huawei_model.const import (
    get_int_dat,
    BYTES_ORDER,
    ShelfType,
    AdjustType,
    LockSpaceType,
    DetectType,
    MoveType,
    ChargeFlag,
    ShelfAnglePolicy,
    ProtocolFormat,
    ChargeMaintain,
)

_logger = logging.getLogger(__name__)


@MiscUtils.singleton
class HuaweiProtocol:
    def __init__(self):
        _logger.info('create huawei protocol')

    def pack_header(
        self,
        msg_len,
        msg_type,
        msg_sn,
        msg_version=PROTOCOL_VERSION,
        encrypt=0x0,
        protocol_format=0x0,
    ):
        header = bytearray('GBP$', 'utf-8')
        header.extend(msg_len.to_bytes(2, byteorder=BYTES_ORDER))
        header.extend(msg_type.to_bytes(2, byteorder=BYTES_ORDER))
        header.extend(msg_sn.to_bytes(4, byteorder=BYTES_ORDER))
        header.append(msg_version)
        header.append(encrypt)  # 加密类型
        header.append(protocol_format)  # 协议内容类型, 0: 二进制结构 1: JSON字节流
        header.extend((0).to_bytes(17, byteorder=BYTES_ORDER))
        return header

    def unpack_header(self, dat) -> dict:
        if len(dat) != MSG_HEADER_LEN:
            _logger.error(f'Invalid msg header len: {len(dat)}')
            return {}

        msg_sn = get_int_dat(dat, 8, 4)
        msg_type = get_int_dat(dat, 6, 2)
        msg_len = get_int_dat(dat, 4, 2)
        return {'type': msg_type, 'sn': msg_sn, 'len': msg_len}

    def pack_alarm_header(
        self, msg_len, msg_type, msg_sn, msg_version=PROTOCOL_ALARM_VERSION, encrypt=0x0
    ):
        header = bytearray('HKP$', 'utf-8')
        header.extend(msg_len.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        header.extend(msg_type.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        header.extend(msg_sn.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        header.append(msg_version)
        header.append(encrypt)  # 加密类型
        header.extend((0).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 保留
        return header

    def unpack_alarm_header(self, dat):
        if len(dat) != ALARM_HEADER_LEN:
            _logger.error(f'Invalid msg header len: {len(dat)}')
            return None

        msg_sn = get_int_dat(dat, 8, 4)
        msg_type = get_int_dat(dat, 6, 2)
        msg_len = get_int_dat(dat, 4, 2)

        Result = namedtuple('Result', 'type sn len')
        return Result(msg_type, msg_sn, msg_len)

    def pack_alarm_request(
        self, device_id, msg_sn, alarm_category, alarm_code, alarm_status, alarm_level, x=0, y=0
    ):
        ba = self.pack_alarm_header(
            msg_len=MSG_HEADER_LEN, msg_type=REQ_UPLOAD_ALARM, msg_sn=msg_sn
        )
        ba.extend(device_id.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 设备id
        ba.extend((0).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 未使用
        ba.extend(alarm_category.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 告警大类
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # process
        ba.append(alarm_status)  # 0: 结束　1: 开始 2: 脉冲; 例如急停时传１，解除急停后传０
        ba.append(alarm_level)
        ba.extend((0).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 未使用
        ba.extend(alarm_code.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 告警次类型
        ba.extend(x.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))  # x坐标
        ba.extend(y.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))

        ba.extend((0).to_bytes(16, byteorder=BYTES_ORDER))  # 保留
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))  # 错误码x码值
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))  # 错误码y码值
        self.update_msg_len(ba)
        return ba

    def unpack_alarm_request(self, dat):
        device_id = get_int_dat(dat, 0, BA_LEN_2)
        alarm_category = get_int_dat(dat, 4, BA_LEN_4)
        alarm_status = get_int_dat(dat, 12, 1)
        alarm_grade = get_int_dat(dat, 13, 1)
        alarm_code = get_int_dat(dat, 16, 4)
        x = get_int_dat(dat, 20, BA_LEN_4)
        y = get_int_dat(dat, 24, BA_LEN_4)

        Alarm = namedtuple('AlarmDat', 'device_id category type_code status grade x y')
        return Alarm(device_id, alarm_category, alarm_code, alarm_status, alarm_grade, x, y)

    def pack_alarm_response(self, msg_sn, result=RESPONSE_OKAY):
        ba = self.pack_alarm_header(
            msg_len=MSG_HEADER_LEN, msg_type=RSP_UPLOAD_ALARM, msg_sn=msg_sn
        )
        ba.extend(result.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def unpack_alarm_response(self, dat):
        result = get_int_dat(dat, 0, 4)
        result_code = get_int_dat(dat, 4, 4)
        return result, result_code

    # 安全加密通道
    def pack_security_channel_request(
        self, device_id, msg_sn, device_type=DeviceType.NONE, device_state=NavigationMode.SLAM
    ):
        ba = self.pack_header(MSG_HEADER_LEN + 12, MSG_REQ_REGISTER, msg_sn)
        ba.extend(device_id.to_bytes(4, byteorder=BYTES_ORDER))
        ba.append(device_type)
        ba.append(device_state)
        ba.append(0x00)
        ba.append(0x00)
        ba.extend(DEVICE_VENDOR_ID.to_bytes(4, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    # 注册请求封包
    def pack_register_request(
        self,
        device_id,
        msg_sn,
        device_type=DeviceType.NONE,
        device_state=NavigationMode.SLAM,
        device_vendor=DEVICE_VENDOR_ID,
        device_sn=DEVICE_SN,
        device_len=750,
        device_width=550,
        device_height=400,
        device_rotate_dia=1000,
        device_weight=100,
    ):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_REGISTER, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(device_vendor.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))

        ba_sn = bytearray(48)
        sn_temp = str.encode(device_sn, 'utf-8')
        ba_sn[0 : len(sn_temp)] = sn_temp[0:]
        ba.extend(ba_sn)

        ba.append(device_type)
        ba.append(device_state)
        ba.extend(device_len.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend(device_width.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend(device_height.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend(device_rotate_dia.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend(device_weight.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    # 注册应答封包
    def pack_register_resp(self, device_id, msg_sn, result, err_code, dm_code='XY'):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_RSP_REGISTER, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(result.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.append(err_code)
        ba.extend(str.encode(dm_code))
        ba.append(0)
        self.update_msg_len(ba)
        return ba

    # 注册应答解包
    def unpack_register_rsp(self, dat):
        if len(dat) != 12:
            _logger.error(f'Invalid data length {len(dat)}')
            return {}
        result = get_int_dat(dat, 4, BA_LEN_4)
        err_code = get_int_dat(dat, 8, 1)
        dm_code = str(dat[9:11], 'utf-8')
        # TODO 根据地码类型对应到地图
        # result = self.unpack_header(response[dat_len-1:dat_len-MSG_HEADER_LEN])
        return {'result': result, 'error': err_code, 'dm_code': dm_code}

    def pack_cfg_upload_status_req(self, device_id, msg_sn):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_CFG_UPLOAD_STATUS, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((200).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((200).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((200).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        return ba

    def unpack_cfg_upload_status_req(self, dat):
        if len(dat) != 16:
            _logger.error(f'Invalid data length {len(dat)}')
            return None
        upload_interval = get_int_dat(dat, 4, BA_LEN_4)  # 单位ms
        distance = get_int_dat(dat, 4, BA_LEN_4)  # 单位mm
        angle = get_int_dat(dat, 4, BA_LEN_4)  # 单位1/1000 degree
        return {'interval': upload_interval, 'distance': distance, 'angle': angle}

    def pack_cfg_warning_server_req(self, device_id, msg_sn):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_CFG_WARN_SERVER, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        # ipv4 地址
        ba.extend(inet_aton('127.0.0.1'))
        # ipv6地址
        ba.extend(inet_pton(AF_INET6, '2001:0db8:85a3:08d3:1319:8a2e:0370:7344'))
        ba.extend((8788).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def unpack_cfg_warning_server_req(self, dat):
        if len(dat) < 28:
            _logger.error(f'unpack_cfg_warning_server_req(): Invalid data length {len(dat)}')
            return None
        str_ipv4 = inet_ntop(AF_INET, dat[4:8])
        str_ipv6 = inet_ntop(AF_INET6, dat[8:24])
        port = get_int_dat(dat, 24, 2)
        return {'ipv4': str_ipv4, 'ipv6': str_ipv6, 'port': port}

    def unpack_cfg_time_sync_req(self, dat):
        if len(dat) < 44:
            _logger.error(f'unpack_cfg_time_sync_req(): Invalid data length {len(dat)}')
            return None
        sync_type = get_int_dat(dat, 4, 1)
        str_ipv4 = inet_ntop(AF_INET, dat[8:12])
        str_ipv6 = inet_ntop(AF_INET6, dat[12:28])
        port = get_int_dat(dat, 28, 2)
        interval = get_int_dat(dat, 30, 2)
        timezone = get_int_dat(dat, 32, 4)
        cur_time = get_int_dat(dat, 36, 8)
        return {
            'sync_type': sync_type,
            'ipv4': str_ipv4,
            'ipv6': str_ipv6,
            'port': port,
            'interval': interval,
            'timezone': timezone,
            'cur_time': cur_time,
        }

    def unpack_cfg_global_precision(self, dat):
        if len(dat) < 8:
            _logger.error(f'unpack_cfg_global_precision(): Invalid data length {len(dat)}')
            return None
        no_payload_move = get_int_dat(dat, 4, 1)  # 单位mm
        payload_move = get_int_dat(dat, 5, 1)
        no_payload_raise = get_int_dat(dat, 6, 1)
        payload_raise = get_int_dat(dat, 7, 1)
        return {
            'no_load_move': no_payload_move,
            'load_move': payload_move,
            'no_load_raise': no_payload_raise,
            'load_raise': payload_raise,
        }

    def pack_cfg_upload_dmcode(self, device_id, msg_sn, upload_flag):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_CFG_UPLOAD_DMCODE, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.append(upload_flag)
        ba.extend((0).to_bytes(3, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def unpack_cfg_upload_dmcode(self, dat):
        if len(dat) < 8:
            return False
        return dat[4] > 0

    def unpack_cfg_timeout(self, dat):
        if len(dat) < 20:
            _logger.error(f'unpack_cfg_timeout(): Invalid data length {len(dat)}')
            return None, None
        live_time = get_int_dat(dat, 4, 0)
        timeout = get_int_dat(8, 2)
        return live_time, timeout

    def unpack_cfg_movement(self, dat):
        # 暂时不需要配置信息
        pass
        # if len(dat) < 44:
        #     _logger.error("Illegal dat length of cfg movement")
        #     return None
        # param_type = get_int_dat(dat, 4, 1)

    def unpack_cfg_capacity(self, dat):
        if len(dat) < 4:
            _logger.error('Illegal len of cfg capacity')
            return False, True
        dispatch_task_ahead = get_int_dat(dat, 4, 1) > 0
        is_need_lock_space = get_int_dat(dat, 5, 1) == 0
        return dispatch_task_ahead, is_need_lock_space

    def unpack_cfg_upload_battery(self, dat):
        if len(dat) < 8:
            _logger.error(f'unpack_cfg_upload_battery(): Invalid data length {len(dat)}')
            return None
        interval = get_int_dat(dat, 4, BA_LEN_2)
        return {'interval': interval / 1000}

    def unpack_changed_map_req(self, dat):
        if len(dat) < 48:
            _logger.error('unpack_changed_map_req(): invalid data length')
            return None

        str_ipv4 = inet_ntop(AF_INET, dat[4:8])
        str_ipv6 = inet_ntop(AF_INET6, dat[8:24])
        port = get_int_dat(dat, 24, 2)
        dmcode_type = str(dat[26:28], 'utf-8')
        x = get_int_dat(dat, 28, 4)
        y = get_int_dat(dat, 32, 4)
        x_factor = get_int_dat(dat, 36, 4)
        y_factor = get_int_dat(dat, 40, 4)
        angle_offset = get_int_dat(dat, 44, 4)
        return {
            'ipv4': str_ipv4,
            'ipv6': str_ipv6,
            'port': port,
            'dmcode_type': dmcode_type,
            'x': x,
            'y': y,
            'x_factor': x_factor,
            'y_factor': y_factor,
            # "angle_offset": 0  # TODO系统问题
            'angle_offset': int(angle_offset / 1000),
        }

    def unpack_changed_switch_req(self, dat):
        change_type = get_int_dat(dat, 4, 1)
        if change_type == NAV_FROM_DMCODE_TO_SLAM:
            cur_x = get_int_dat(dat, 8, 4)
            cur_y = get_int_dat(dat, 12, 4)
            angle_offset = get_int_dat(dat, 16, 4)
            dmcode_type = str(dat[22:24], 'utf-8')
            _logger.info(
                f'cur_x:{cur_x},cur_y:{cur_y},angle_offset:{angle_offset},dmcode_type:{dmcode_type}'
            )
            return {
                'x': cur_x,
                'y': cur_y,
                'angle': angle_offset,
                'dmcode_type': dmcode_type,
            }
        elif change_type == NAV_FROM_SLAM_TO_DMCODE:
            return {'x': 0}

    def pack_change_map_req(
        self, device_id, msg_sn, dmcode_type: str, ip: str, port: int, x, y, angle_offset
    ):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_CHANGE_MAP, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(inet_aton(ip))
        ba.extend((0).to_bytes(16, byteorder=BYTES_ORDER))
        ba.extend((port).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend(str.encode(dmcode_type))
        ba.extend(x.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(y.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend((10).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend((20).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(angle_offset.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        self.update_msg_len(ba)
        return ba

    def pack_force_shelf_action(self, device_id, msg_sn, action_type=SHELF_FORCE_RAISE, height=0):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_SHELF_ACTION_FORCE, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.append(action_type)
        ba.append(0)
        ba.extend(height.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def unpack_force_shelf_action(self, dat):
        if len(dat) < 8:
            _logger.error('Invalid dat len')
            return None
        ctrl_type = dat[4]
        height = 1000
        return ctrl_type, int(height / 10)  # 0.1mm -> mm

    # 设备能力集请求
    def pack_device_ability_req(self, device_id, msg_sn):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_DEVICE_ABILITY, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    # 上传设备能力集
    def pack_upload_device_ability(self, device_id, msg_sn):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_UPLOAD_ABILITY, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((200).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 负载能力(kg)
        ba.append(24)  # 续航能力(hour)
        ba.append(0)  # 是否带称重传感器
        ba.append(30)  # 空载精度(mm)
        ba.append(50)  # 载货精度
        ba.append(30)  # 空车举升精度
        ba.append(50)  # 载货举升精度

        move_performance = self.get_device_move_performance()
        ba.extend(move_performance)  # 空车运动性能
        ba.extend(move_performance)  # 额定负载运动性能
        self.update_msg_len(ba)
        return ba

    # 设备移动性能
    def get_device_move_performance(self):
        ba = bytearray()
        ba.extend(
            (300).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True)
        )  # 直线加速度(mm/s^2)
        ba.extend((300).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))  # 直线减速度
        ba.extend((1500).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))  # 最大线速度(mm/s)
        ba.extend(
            (500).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True)
        )  # 角加速度(1/1000 deg/s^2)
        ba.extend((500).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))  # 角减速度
        ba.extend(
            (45000).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True)
        )  # 最大角速度(1/1000 deg/s)
        ba.extend(
            (200).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True)
        )  # 弧线加速度(mm/s^2)
        ba.extend((200).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))  # 弧线减速度
        ba.extend(
            (800).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True)
        )  # 最大弧线速度(mm/s)
        return ba

    # 上传状态
    def pack_status_upload_req(
        self,
        device_id,
        msg_sn,
        task_id,
        subtask_id,
        system_state,
        x,
        y,
        angle,
        linear_velocity,
        battery_level,
        battery_temperature,
        battery_current,
        battery_voltage,
        linear_acc_velocity=0,
        linear_dec_velocity=0,
        angular_velocity=0,
        acc_angular=0,
        dmcode_type='',
        upgrade_state=0,
        download_state=0,
        main_warning=0,
        sub_waring=0,
    ):
        if task_id < 0:
            task_id = 0
        if subtask_id < 0:
            subtask_id = 0

        ba = self.pack_header(MSG_HEADER_LEN + 64, MSG_REQ_UPLOAD_STATE, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(task_id.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.append(subtask_id)
        ba.append(0x00)  # 保留
        ba.extend(system_state.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(x.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(y.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(angle.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(linear_velocity.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(linear_acc_velocity.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(linear_dec_velocity.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(angular_velocity.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(acc_angular.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        if dmcode_type == '':
            ba.extend((0).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        else:
            ba.extend(str.encode(dmcode_type))
        ba.append(upgrade_state)
        ba.append(download_state)
        ba.extend(main_warning.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend(sub_waring.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))

        ba.extend(battery_temperature.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend(battery_current.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER, signed=True))
        ba.extend(battery_voltage.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER, signed=True))
        ba.append(battery_level)
        ba.append(0)  # 保留
        ba.extend((0).to_bytes(47, byteorder=BYTES_ORDER))  # 预留

        # ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def pack_version_upload_req(self, device_id, msg_sn, json_dat, pkg_cnt=1, pkg_idx=0):
        ba = self.pack_header(
            MSG_HEADER_LEN, MSG_REQ_UPLOAD_VERSIONS, msg_sn, protocol_format=ProtocolFormat.Json
        )
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.append(pkg_cnt)
        ba.append(pkg_idx)
        ba.extend((0).to_bytes(2, byteorder=BYTES_ORDER))
        ba.extend(str.encode(json.dumps(json_dat)))
        self.update_msg_len(ba)
        return ba

    def pack_upload_battery_status_req(self, device_id, msg_sn, battery_info):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_UPLOAD_BATTERY_STATUS, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.append(battery_info['percent'])  # 电池电量
        ba.append(0)
        ba.extend(
            battery_info['voltage'].to_bytes(BA_LEN_2, byteorder=BYTES_ORDER)
        )  # 电池电压, 1/100V
        if battery_info['current'] >= 0:
            ba.extend(int(0).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 输入电流, 1/10A
            ba.extend(
                int(battery_info['current']).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER)
            )  # 输出电流
        else:
            ba.extend(
                int(0 - battery_info['current']).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER)
            )  # 输入电流, 1/10A
            ba.extend(int(0).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 输出电流
        ba.extend(
            battery_info['temperature'].to_bytes(BA_LEN_2, byteorder=BYTES_ORDER, signed=True)
        )  # 最高温度, 1/10℃
        ba.extend(
            battery_info['temperature'].to_bytes(BA_LEN_2, byteorder=BYTES_ORDER, signed=True)
        )  # 最低温度
        ba.extend(
            battery_info['voltage'].to_bytes(BA_LEN_2, byteorder=BYTES_ORDER, signed=True)
        )  # 最高单体电压1/1000V
        ba.extend(
            battery_info['voltage'].to_bytes(BA_LEN_2, byteorder=BYTES_ORDER, signed=True)
        )  # 最低单体电压
        ba.extend(
            battery_info['cycle_times'].to_bytes(BA_LEN_2, byteorder=BYTES_ORDER)
        )  # 循环使用次数
        ba.extend(battery_info['capacity'].to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 容量
        self.update_msg_len(ba)
        return ba

    def pack_upload_dmcode_req(self, device_id, msg_sn, robot_angle, dmcode):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_UPLOAD_DMCODE, msg_sn)

        timestamp = round(time.time())  # 单位s
        robot_angle = int(robot_angle * 1000)  # 度->1/1000度
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(robot_angle.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))

        ba_dm_code = bytearray(32)
        dm_code_temp = str.encode(dmcode, 'utf-8')
        ba_dm_code[0 : len(dm_code_temp)] = dm_code_temp[0:]
        ba.extend(ba_dm_code)
        ba.extend(timestamp.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    # 执行机构数据, 不附加任何信息
    def pack_none_actuator_status(self, dat):
        dat.append(ActuatorIdx.NONE)
        self.update_msg_len(dat)
        return dat

    def pack_shelf_actuator_status(
        self, dat, shelf_id, status, shelf_x=0, shelf_y=0, shelf_angle: float = 0
    ):
        dat.append(ActuatorIdx.GOODS)  # 货物信息

        shelf_angle = int(shelf_angle * 1000)
        ba_shelf_id = bytearray(32)
        shelf_id_temp = str.encode(shelf_id, 'utf-8')
        ba_shelf_id[0 : len(shelf_id_temp)] = shelf_id_temp[0:]
        dat.extend(ba_shelf_id)

        dat.extend(shelf_x.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        dat.extend(shelf_y.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        dat.extend(shelf_angle.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        dat.append(status)
        dat.extend((0).to_bytes(3, byteorder=BYTES_ORDER, signed=True))
        self.update_msg_len(dat)
        return dat

    def pack_arm_status(self, dat, is_executing_action, load_state, arm_load_array):
        dat.append(ActuatorIdx.ARM)
        dat.append(load_state)
        dat.append(6)
        assert len(arm_load_array) == 10
        dat.extend(arm_load_array)
        if is_executing_action:
            dat.append(2)
        else:
            dat.append(1)
        dat.extend(bytearray(17))  # 保留
        dat.extend(bytearray(24))  # 末端位置
        dat.extend(bytearray(64))  # 关节位置

    def pack_gulf_status(self, dat, fork_height, load_state):
        dat.append(ActuatorIdx.GULF)
        dat.extend(fork_height.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        dat.append(load_state)
        dat.extend((0).to_bytes(51, byteorder=BYTES_ORDER))

    def pack_smt_status(self, dat, smt_state: SmtState):
        # NOTE: 10.14.1 任务上报

        dat.append(ActuatorIdx.SMT)
        for unit in smt_state.units:
            dat.append(unit.index)
            dat.append(unit.docking_state)
            dat.append(unit.cargo_state)
            dat.append(unit.action_type)
            dat.append(unit.action_direction)
            dat.extend(unit.lift_height.to_bytes(2, byteorder=BYTES_ORDER, signed=True))
            dat.extend(unit.lift_speed.to_bytes(2, byteorder=BYTES_ORDER))
            dat.extend(unit.adjust_width.to_bytes(2, byteorder=BYTES_ORDER))
            dat.extend(unit.adjust_width_speed.to_bytes(2, byteorder=BYTES_ORDER))
            dat.append(unit.cargo_type)
            dat.extend((0).to_bytes(18, byteorder=BYTES_ORDER))

    def pack_smt_ctrl_info(self, dat, smt_info: SmtInfo):
        # NOTE: 10.1.4.3 执行机构信息
        dat.extend(ActuatorIdx.SMT.to_bytes(2, byteorder=BYTES_ORDER))
        dat.extend((0).to_bytes(6, byteorder=BYTES_ORDER))
        for unit in smt_info.units:
            dat.append(unit.index)
            dat.append(unit.action_type)
            dat.append(unit.action_direction)
            dat.append(0)
            dat.extend(unit.lift_height.to_bytes(2, byteorder=BYTES_ORDER, signed=True))
            dat.extend(unit.lift_speed.to_bytes(2, byteorder=BYTES_ORDER))
            dat.extend(unit.adjust_width.to_bytes(2, byteorder=BYTES_ORDER))
            dat.extend(unit.adjust_width_speed.to_bytes(2, byteorder=BYTES_ORDER))
            dat.append(unit.cargo_type)
            dat.extend((0).to_bytes(11, byteorder=BYTES_ORDER))

    def pack_shelf_actuator_detect_ctrl(self, dat, shelf_sn, angle):
        dat.append(ActuatorIdx.SHELF)  # 探测货架
        shelf_angle = AngleUtils.normalize_180(angle)
        shelf_angle = int(shelf_angle * 1000)

        ba_shelf_id = bytearray(32)
        shelf_id_temp = str.encode(shelf_sn, 'utf-8')
        ba_shelf_id[0 : len(shelf_id_temp)] = shelf_id_temp[0:]
        dat.extend(ba_shelf_id)
        dat.extend(shelf_angle.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
        self.update_msg_len(dat)
        return dat

    def pack_execute_smt_req(
        self,
        device_id,
        msg_sn,
        x,
        y,
        angle,
        points_groups,
        smt_ctrl_info,
        task_id=1,
        sub_task_id=1,
        type_code=MSG_REQ_LINEAR_NO_PAYLOAD_MULTI_PATH_MOVE,
        move_with_action=0,
    ):
        dat = self.pack_multi_no_payload_move(
            device_id=device_id,
            msg_sn=msg_sn,
            x=x,
            y=y,
            angle=angle,
            points_groups=points_groups,
            task_id=task_id,
            sub_task_id=sub_task_id,
            type_code=type_code,
            move_with_action=move_with_action,
        )
        self.pack_smt_ctrl_info(dat, smt_info=smt_ctrl_info)
        self.update_msg_len(dat)
        return dat

    def pack_shelf_sn_detect_req(
        self,
        device_id,
        msg_sn,
        x,
        y,
        angle,
        continue_time: int = 8,
        detect_type: int = DetectType.Default,
    ):
        """
        探测货架打包
        :param device_id: 设备id
        :param msg_sn: 信息id
        :param x: （mm）
        :param y: （mm）
        :param angle: 角度
        :param continue_time: 协议默认值为8秒,有效范围为[8,255]
        :param detect_type: 探测类型,当前定义: 0x0, 0x1, 0x2
        :return: 十六进制数据
        """
        dat = self.pack_no_payload_linear_move_req(
            device_id, msg_sn, x, y, angle, MSG_REQ_DETECT_CTRL
        )
        dat.extend(detect_type.to_bytes(2, byteorder=BYTES_ORDER))
        dat.append(continue_time)
        dat.append(0x0)
        self.update_msg_len(dat)
        return dat

    def pack_roller_status(self, dat, roller0=0, roller1=0, roller2=0, roller3=0):
        dat.append(ActuatorIdx.ROLLER)
        dat.append(roller0)  # 滚筒0货物数量
        dat.append(roller1)
        dat.append(roller2)
        dat.append(roller3)
        dat.extend((0).to_bytes(44, byteorder=BYTES_ORDER))
        self.update_msg_len(dat)
        return dat

    # 上传状态应答
    def pack_status_upload_rsp(self, device_id, msg_sn, result, err_code):
        return self.pack_common_rsp(
            device_id=device_id,
            msg_sn=msg_sn,
            type_code=MSG_RSP_UPLOAD_STATE,
            result=result,
            err_code=err_code,
        )

    # 空间锁格
    def pack_lock_space_req(
        self,
        device_id,
        msg_sn,
        x,
        y,
        lock_type=LockSpaceType.NO_PAYLOAD_ROTATE,
        lock_length=0,
        lock_width=0,
    ):
        # _logger.info("lock space %d %d %d %d %d" % (x, y, lock_type, lock_length, lock_width))
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_LOCK_SPACE, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.append(5)  # 优先级
        ba.append(lock_type)
        ba.extend((0).to_bytes(2, byteorder=BYTES_ORDER))  # 保留
        ba.extend(x.to_bytes(4, byteorder=BYTES_ORDER, signed=True))  # 当前坐标
        ba.extend(y.to_bytes(4, byteorder=BYTES_ORDER, signed=True))

        # 锁格区域,　叉车专用,暂时不设置
        ba.extend(x.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(y.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(lock_width.to_bytes(4, byteorder=BYTES_ORDER, signed=False))
        ba.extend(lock_length.to_bytes(4, byteorder=BYTES_ORDER, signed=False))
        # ba.extend((0).to_bytes(16, byteorder=BYTES_ORDER))  # 保留

        self.update_msg_len(ba)
        return ba

    def unpack_lock_space_req(self, dat):
        if len(dat) != 32:
            return {}
        lock_type = get_int_dat(dat, 5, 1)
        cur_x = get_int_dat(dat, 8, 4)
        cur_y = get_int_dat(dat, 12, 4)
        return {'lock_type': lock_type, 'cur_x': cur_x, 'cur_y': cur_y}

    # 空间解锁
    def pack_unlock_space_req(self, device_id, msg_sn, x, y):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_UNLOCK_SPACE, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(x.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(y.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
        ba.extend((0).to_bytes(16, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    # 空间锁格
    def pack_lock_space_rsp(self, device_id, msg_sn, type_code, result=1, err_code=0):
        ba = self.pack_header(MSG_HEADER_LEN, type_code, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.append(result)
        ba.append(err_code)
        ba.extend((0).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER, signed=True))
        self.update_msg_len(ba)
        return ba

    def pack_move_ctrl_req(self, device_id, msg_sn, type_code):
        ba = self.pack_header(MSG_HEADER_LEN, type_code, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    # 空间解锁
    def unpack_lock_space_rsp(self, dat):
        if len(dat) != 8:
            return None
        result = get_int_dat(dat, 4, 1)
        err_code = get_int_dat(dat, 5, 1)
        return {'result': result, 'error': err_code}

    # 空车直线运动
    def pack_no_payload_linear_move_req(
        self,
        device_id,
        msg_sn,
        x,
        y,
        angle,
        type_code=MSG_REQ_NO_PAYLOAD_LINEAR_MOVE,
        task_id=1,
        sub_task_id=1,
        task_type=TaskItem.Normal,
        limit_v=1000,
        stop_distance=100,
    ):
        return self.pack_common_move_target(
            device_id,
            msg_sn,
            x,
            y,
            angle,
            type_code,
            task_id=task_id,
            sub_task_id=sub_task_id,
            task_type=task_type,
            max_velocity=limit_v,
            stop_distance=stop_distance,
        )

    def pack_execute_roller_req(
        self,
        device_id,
        msg_sn,
        x,
        y,
        angle,
        roller0,
        roller1,
        roller2,
        roller3,
        task_id=1,
        sub_task_id=1,
    ):
        ba = self.pack_common_move_target(
            device_id=device_id,
            msg_sn=msg_sn,
            x=x,
            y=y,
            angle=angle,
            type_code=MSG_REQ_ROLLER_CTRL,
            task_id=task_id,
            sub_task_id=sub_task_id,
        )
        ba.append(roller0.action_type)
        ba.append(roller0.direction)
        ba.append(roller0.cargo_count)
        ba.append(0)
        ba.append(roller1.action_type)
        ba.append(roller1.direction)
        ba.append(roller1.cargo_count)
        ba.append(0)
        ba.append(roller2.action_type)
        ba.append(roller2.direction)
        ba.append(roller2.cargo_count)
        ba.append(0)
        ba.append(roller3.action_type)
        ba.append(roller3.direction)
        ba.append(roller3.cargo_count)
        ba.append(0)
        self.update_msg_len(ba)
        return ba

    # 空车直线运动
    def pack_execute_shelf_req(
        self,
        device_id,
        msg_sn,
        x=100,
        y=200,
        angle=90,
        shelf_id_str='',
        shelf_type=ShelfType.Rectangle,
        type_code=MSG_REQ_RAISE_SHELF,
        task_type=TaskItem.Normal,
        shelf_moving_policy=ShelfAnglePolicy.Ignore,
        shelf_target_angle=ShelfAnglePolicy.Ignore,
        arc_points=None,
        points_groups=None,
        adjust_type=AdjustType.NO_LIMIT,
        task_id=1,
        sub_task_id=1,
    ):
        ba = self.pack_common_move_target(
            device_id,
            msg_sn,
            x,
            y,
            angle,
            type_code,
            task_type=task_type,
            task_id=task_id,
            sub_task_id=sub_task_id,
        )
        assert not (arc_points is not None and points_groups is not None), (
            '曲线控制点和多路径控制点不能同时存在'
        )
        if arc_points:
            ba.append(len(arc_points))
            ba.extend((0).to_bytes(3, byteorder=BYTES_ORDER))
            for p in arc_points:
                ba.extend(p.to_dat())
                ba.extend((0).to_bytes(20, byteorder=BYTES_ORDER))
            # 预留数据
            ba.extend((0).to_bytes(6 * BYTE_NUM_POINT_INFO, byteorder=BYTES_ORDER))
        elif points_groups:
            ba.append(len(points_groups))
            ba.append(0)
            ba.extend((480).to_bytes(2, byteorder=BYTES_ORDER))
            for points_group in points_groups:
                ba.extend((500).to_bytes(2, byteorder=BYTES_ORDER))
                ba.extend((1000).to_bytes(2, byteorder=BYTES_ORDER))
                ba.append(points_group[0].point_type)
                ba.append(len(points_group))
                ba.append(0)
                ba.extend((0).to_bytes(9, byteorder=BYTES_ORDER))
                for point in points_group:
                    ba.extend(point.x.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
                    ba.extend(point.y.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
                print('path len', len(points_group))
                ba.extend((0).to_bytes((80 - 8 * len(points_group)), byteorder=BYTES_ORDER))
            print('path count', len(points_groups))
            ba.extend((0).to_bytes((480 - 96 * len(points_groups)), byteorder=BYTES_ORDER))
        # 执行结构信息
        ba.extend((0).to_bytes(28, byteorder=BYTES_ORDER))

        # 货物信息
        ba_shelf_id = bytearray(32)
        shelf_id_temp = str.encode(shelf_id_str, 'utf-8')
        ba_shelf_id[0 : len(shelf_id_temp)] = shelf_id_temp[0:]
        ba.extend(ba_shelf_id)

        ba.append(shelf_type)
        ba.append(3)  # 举货架精度
        ba.append(adjust_type)  # 调整类型
        ba.append(0)
        ba.extend((50).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 举升高度
        ba.extend((0).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend(
            shelf_moving_policy.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True)
        )  # 货架移动角度
        ba.extend(shelf_target_angle.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 货架目标角度
        ba.extend((1500).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 货架长度
        ba.extend((800).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((100).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.append(0)  # 放货架精度
        ba.append(0)

        # 货码偏移
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))

        self.update_msg_len(ba)
        return ba

    def pack_charge_req(self, device_id, msg_sn, x, y, angle):
        ba = self.pack_common_move_target(
            device_id,
            msg_sn,
            x,
            y,
            angle,
            move_type=MoveType.Backward,
            type_code=MSG_REQ_CHARGE,
            task_type=TaskItem.Charge,
        )
        ba.extend(ChargeFlag.Start_Charge.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 充电标志
        ba.extend((1).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 充电时间
        ba.extend((100).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 充电桩id
        ba.extend((100).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 保留
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 保留
        self.update_msg_len(ba)
        return ba

    def pack_stop_charge_req(self, device_id, msg_sn, x, y, angle):
        ba = self.pack_common_move_target(
            device_id,
            msg_sn,
            x,
            y,
            angle,
            move_type=MoveType.Backward,
            type_code=MSG_REQ_CHARGE,
            task_type=TaskItem.Charge,
        )
        ba.extend(ChargeFlag.Stop_Charge.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 充电标志
        ba.extend((1).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 充电时间
        ba.extend((100).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 充电桩id
        ba.extend((100).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 保留
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 保留
        self.update_msg_len(ba)
        return ba

    def pack_arc_no_payload_move(
        self, device_id, msg_sn, x, y, angle, points, task_id=1, sub_task_id=1
    ):
        ba = self.pack_common_move_target(
            device_id,
            msg_sn,
            x,
            y,
            angle,
            MSG_REQ_NO_PAYLOAD_ARC_MOVE,
            task_id=task_id,
            sub_task_id=sub_task_id,
        )
        ba.append(len(points))
        ba.extend((0).to_bytes(3, byteorder=BYTES_ORDER))
        for p in points:
            ba.extend(p.to_dat())
            ba.extend((0).to_bytes(20, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def pack_multi_no_payload_move(
        self,
        device_id,
        msg_sn,
        x,
        y,
        angle,
        points_groups,
        task_id=1,
        sub_task_id=1,
        type_code=MSG_REQ_LINEAR_NO_PAYLOAD_MULTI_PATH_MOVE,
        move_with_action=0,
    ):
        # 直接取第一段路径的限速
        limit_v = points_groups[0][0].limit_v if points_groups and points_groups[0] else 0

        ba = self.pack_common_move_target(
            device_id,
            msg_sn,
            x,
            y,
            angle,
            type_code,
            task_id=task_id,
            sub_task_id=sub_task_id,
            max_velocity=limit_v,
            move_with_action=move_with_action,
        )
        ba.append(len(points_groups))
        ba.append(0)
        ba.extend((480).to_bytes(2, byteorder=BYTES_ORDER))
        for points_group in points_groups:
            ba.extend(points_group[-1].limit_v.to_bytes(2, byteorder=BYTES_ORDER))
            ba.extend((1000).to_bytes(2, byteorder=BYTES_ORDER))
            ba.append(points_group[0].point_type)
            ba.append(len(points_group))
            ba.append(0)
            ba.extend((0).to_bytes(9, byteorder=BYTES_ORDER))
            for point in points_group:
                ba.extend(point.x.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
                ba.extend(point.y.to_bytes(4, byteorder=BYTES_ORDER, signed=True))
            ba.extend((0).to_bytes((80 - 8 * len(points_group)), byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes((480 - 96 * len(points_groups)), byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def pack_arm_action(self):
        ba = self.pack_common_move_target(
            0, 111, 0, 0, 0, MSG_REQ_ARM_FORK_LOAD_ACTION, task_id=1, sub_task_id=1
        )
        ba.append(0)
        ba.append(0)
        ba.extend((480).to_bytes(2, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(480, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(2, byteorder=BYTES_ORDER))
        ba_shelf_id = bytearray(8)
        shelf_id_temp = str.encode('123ad321', 'utf-8')
        ba_shelf_id[0 : len(shelf_id_temp)] = shelf_id_temp[0:]
        ba.extend(ba_shelf_id)
        ba.extend((0).to_bytes(52, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def pack_fork_load_action(self):
        ba = self.pack_common_move_target(
            0,
            111,
            0,
            0,
            0,
            0x32A,
            move_type=MoveType.Forward,
            task_type=TaskItem.Fork_Unload_Action_Go_DOCK,
            task_id=1,
            sub_task_id=1,
        )
        ba.extend((480).to_bytes(2, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(480, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(2, byteorder=BYTES_ORDER))

        # 执行结构信息
        ba.extend((0).to_bytes(2, byteorder=BYTES_ORDER))
        ba.extend((1800).to_bytes(2, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(24, byteorder=BYTES_ORDER))

        # 货物信息
        ba_shelf_id = bytearray(32)
        shelf_id_temp = str.encode('123ad321', 'utf-8')
        ba_shelf_id[0 : len(shelf_id_temp)] = shelf_id_temp[0:]
        ba.extend(ba_shelf_id)

        ba.append(1)
        ba.append(3)  # 举货架精度
        ba.append(0)  # 调整类型
        ba.append(0)
        ba.extend((50).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 举升高度
        ba.extend((0).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend(
            ShelfAnglePolicy.Ignore.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True)
        )  # 货架移动角度
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 货架目标角度
        ba.extend((1500).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 货架长度
        ba.extend((800).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((100).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.append(0)  # 放货架精度
        ba.append(0)

        # 货码偏移
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        return ba

    def pack_charge_full_req(self, device_id, msg_sn, type_code=ChargeMaintain.ChargeTaskMaintain):
        ba = self.pack_header(MSG_HEADER_LEN + 8, MSG_REQ_CHARGE_MAINTAIN, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.append(type_code)
        ba.extend((0).to_bytes(3, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    # 空车直线运动
    def pack_common_move_target(
        self,
        device_id,
        msg_sn,
        x,
        y,
        angle,
        type_code,
        target_type=0x0,
        move_type=MoveType.Forward,
        task_type=TaskItem.Normal,
        move_with_action=0,
        max_velocity=1000,
        task_id=1,
        sub_task_id=1,
        stop_distance=100,
    ):
        ba = self.pack_header(MSG_HEADER_LEN, type_code, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(task_id.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.append(sub_task_id)
        ba.append(move_type)  # 移动类型
        ba.extend(task_type.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 大任务类型
        ba.append(move_with_action)  # 是否移动中同步动作
        ba.append(0)  # 保留
        ba.append(0)  # 是否播放语音
        ba.append(0)  # 是否闪灯
        ba.extend((0).to_bytes(14, byteorder=BYTES_ORDER))  # 保留
        ba.extend(x.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(y.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend(angle.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.append(target_type)  # 目标点/站点类型
        ba.append(0)  # 任务精度等级
        ba.extend((30).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 距离精度
        ba.extend((1000).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 小车角度精度
        ba.extend((1000).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 货架角度精度
        ba.extend(max_velocity.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 全向车移动方向
        ba.extend((0).to_bytes(20, byteorder=BYTES_ORDER))  # 保留
        ba.extend(x.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))  # 最终目标点信息
        ba.extend(y.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))
        # ba.extend(angle.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER, signed=True))

        ba.extend((90).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 距离阈值
        ba.extend((0).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 保留+功能索引
        ba.extend(stop_distance.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 停止区
        ba.extend((10).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend((30).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.extend((40).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))

        ba.extend((100).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 减速区1 + 减速区2，用于测试
        ba.extend((20).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 减速区1 + 减速区2，用于测试
        ba.extend((50).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 减速区1 + 减速区2，用于测试
        ba.extend((60).to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))  # 减速区1 + 减速区2，用于测试
        ba.extend((0).to_bytes(40, byteorder=BYTES_ORDER))  # 减速区1 + 减速区2
        ba.extend((0).to_bytes(8, byteorder=BYTES_ORDER))  # 自定义
        ba.extend((0).to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))  # 保留
        self.update_msg_len(ba)
        return ba

    def pack_no_payload_move_resp(self, device_id, msg_sn, result=RESPONSE_OKAY):
        ba = self.pack_header(MSG_HEADER_LEN + 8, MSG_RSP_NO_PAYLOAD_LINEAR_MOVE, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(result.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def pack_pause_task(self, device_id, msg_sn, task_id, sub_task_id):
        ba = self.pack_header(MSG_HEADER_LEN + 8, MSG_REQ_PAUSE, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(task_id.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.append(sub_task_id)
        ba.append(0)
        self.update_msg_len(ba)
        return ba

    def pack_continue_task(self, device_id, msg_sn, task_id, sub_task_id):
        ba = self.pack_header(MSG_HEADER_LEN + 8, MSG_REQ_CONTINUE, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(task_id.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.append(sub_task_id)
        ba.append(0)
        self.update_msg_len(ba)
        return ba

    def pack_cancel_task(self, device_id, msg_sn, task_id, sub_task_id):
        ba = self.pack_header(MSG_HEADER_LEN + 8, MSG_REQ_CANCEL, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(task_id.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.append(sub_task_id)
        ba.append(0)
        self.update_msg_len(ba)
        return ba

    def pack_stop_move_task(self, device_id, msg_sn, task_id, sub_task_id):
        ba = self.pack_header(MSG_HEADER_LEN + 8, MSG_REQ_STOP_MOVE, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(task_id.to_bytes(BA_LEN_2, byteorder=BYTES_ORDER))
        ba.append(sub_task_id)
        ba.append(0)
        self.update_msg_len(ba)
        return ba

    def unpack_move_req(self, dat, task_type):
        if task_type in (
            TaskType.No_Payload_Linear_Move,
            TaskType.Linear_Move_After_Raise_Shelf,
            TaskType.Linear_Move_After_Put_Shelf,
            TaskType.Raise_Shelf_Action,
            TaskType.Slam_Nav,
            TaskType.Roller_Control,
            TaskType.Charge_Task,
            TaskType.Put_Shelf_Action,
            TaskType.Shelf_SN_Detect,
        ):
            return self.unpack_linear_move_req(dat, task_type)
        elif task_type in (
            TaskType.No_Payload_Arc_Move,
            TaskType.Arc_Move_After_Raise_Shelf,
            TaskType.Arc_Move_After_Put_Shelf,
        ):
            return self.unpack_arc_move_req(dat, task_type)
        elif task_type in (
            TaskType.Multi_Path_No_Payload_Move,
            TaskType.Multi_Path_Move_After_Raise_Shelf,
            TaskType.Multi_Path_Move_After_Put_Shelf,
            TaskType.Arm_Fork_Load_Action,
            TaskType.Arm_Fork_Unload_Action,
            TaskType.Smt_Load_Action,
            TaskType.Smt_Unload_Action,
            TaskType.Smt_Multi_Path_Move,
        ):
            return self.unpack_multi_move_req(dat, task_type)
        else:
            _logger.info('Unknown task type ' + task_type)
        return None

    def unpack_command_req(self, dat, task_type):
        task = CommandTask(task_type)
        task.from_dat(dat)
        return task

    # 直线运动
    def unpack_linear_move_req(self, dat, task_type):
        task = LinearMoveTask(task_type)
        task.from_dat(dat)
        return task

    # 弧线运动
    def unpack_arc_move_req(self, dat, task_type):
        task = ArcMoveTask(task_type)
        task.from_dat(dat)
        return task

    def unpack_multi_move_req(self, dat, task_type):
        task = MultiMoveTask(task_type)
        task.from_dat(dat)
        return task

    def pack_replan_online_req(self, device_id, msg_sn):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_REPLAN_ONLINE, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def unpack_replan_online(self, dat) -> dict:
        result = get_int_dat(dat, 4, 1)
        error_code = get_int_dat(dat, 5, 1)
        return {'result': result, 'error': error_code}

    def unpack_move_rsp(self, dat):
        if len(dat) != 8:
            return None
        result = get_int_dat(dat, 4, 4)
        return {'result': result}

    # def unpack_response_security_channel(self, response):
    #     if len(response) < 4:
    #         return None
    #     result = response[0:3]
    #     return int.from_bytes(result)

    def unpack_upload_status_rsp(self, dat):
        return self.unpack_common_rsp(dat)

    def unpack_upload_status_req(self, dat) -> dict:
        """将上传的系统状态解包"""
        point = Point()
        point.from_dat(dat[12:])
        actuator_idx = get_int_dat(dat, 107, BA_LEN_1)
        data = {
            'device_id': get_int_dat(dat, 0, BA_LEN_4),
            'task_id': get_int_dat(dat, 4, BA_LEN_2),
            'subtask_id': get_int_dat(dat, 6, BA_LEN_1),
            'system_state': get_int_dat(dat, 8, BA_LEN_4),
            'point': point,
            'dmcode_type': dat[44:46].decode('utf-8'),
            'actuator_idx': actuator_idx,
        }
        if actuator_idx in (ActuatorIdx.SHELF, ActuatorIdx.GOODS):
            data['actuator_info'] = self.unpack_shelf_actuator_detect_ctrl_req(dat[108:])
        elif actuator_idx == ActuatorIdx.ROLLER:
            data['actuator_info'] = self.unpack_roller_status(dat[108:])
        elif actuator_idx == ActuatorIdx.SMT:
            data['actuator_info'] = self.unpack_smt_status(dat[108:])
        return data

    def unpack_roller_status(self, dat) -> dict:
        return {'roller0': dat[0], 'roller1': dat[1], 'roller2': dat[2], 'roller3': dat[3]}

    def unpack_smt_status(self, dat) -> dict:
        return {str(i): dat[32 * i : 32 * (i + 1)] for i in range(4)}

    def unpack_shelf_actuator_detect_ctrl_req(self, dat) -> dict:
        valid_idx = dat[0:32].find(b'\x00')
        if valid_idx == -1:
            shelf_id = dat[0:32].decode('utf-8')
        else:
            shelf_id = dat[0:valid_idx].decode('utf-8')
        return {'shelf_id': shelf_id, 'shelf_angle': get_int_dat(dat, 32, BA_LEN_4)}

    def unpack_pack_shelf_actuator_status_req(self, dat) -> dict:
        valid_idx = dat[0:32].find(b'\x00')
        if valid_idx == -1:
            shelf_id = dat[0:32].decode('utf-8')
        else:
            shelf_id = dat[0:valid_idx].decode('utf-8')
        return {'shelf_id': shelf_id, 'shelf_angle': get_int_dat(dat, 40, BA_LEN_4)}

    def pack_notify_changed_map(self, device_id, msg_sn):
        ba = self.pack_header(MSG_HEADER_LEN, MSG_REQ_NOTIFY_MAP_CHANGE, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def pack_common_rsp(self, device_id, msg_sn, type_code, result=RESPONSE_OKAY, err_code=None):
        ba = self.pack_header(MSG_HEADER_LEN, type_code, msg_sn)
        ba.extend(device_id.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))
        ba.extend(result.to_bytes(BA_LEN_4, byteorder=BYTES_ORDER))

        if err_code is not None:
            ba.append(err_code)
            ba.extend((0).to_bytes(3, byteorder=BYTES_ORDER))
        self.update_msg_len(ba)
        return ba

    def unpack_common_rsp(self, dat, has_err_code=True):
        if has_err_code and len(dat) != 12:
            return None
        if not has_err_code and len(dat) != 8:
            return None
        result = get_int_dat(dat, 4, 4)

        err_code = get_int_dat(dat, 8, 1) if has_err_code else 0
        return {'result': result, 'error': err_code}

    def update_msg_len(self, dat):
        ba_len = len(dat).to_bytes(2, byteorder=BYTES_ORDER)
        dat[4] = ba_len[0]
        dat[5] = ba_len[1]
