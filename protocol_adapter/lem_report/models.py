from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field
from typing import Callable, Optional, List

from protocol_adapter.lem_report.const import AutoCheckAction, AutoCheckResult, AutoCheckType
from protocol_adapter.models.settings import TweakSettings
from .models_payload import BaseReqInfo, DeployInfo, AlarmData, AutoCheckData


class PayloadType(Enum):
    Http = 0x1
    Udp = 0x2


class ControlState(Enum):
    """0x0000"""

    Continue = 0x1  # 成功，正常节奏继续扫描
    Pause = 0x10  # 此次上报后暂停上报
    Stop = 0x20  # 此次上报后结束上报


class ReportPayload(BaseModel):
    state: ControlState = Field(
        default=ControlState.Continue, description='控制状态，载荷反馈信息，用于调整上报任务状态'
    )
    skip: bool = Field(default=False, description='是否跳过此次上报')
    type: PayloadType = Field(default=PayloadType.Http, description='载荷对应接口类型')
    value: dict = Field(default_factory=dict, description='载荷数据字典')


class ReportType(Enum):
    AgvStatus = 0x1
    AgvAlarm = 0x2
    AgvMeasure = 0x3
    AgvAutoCheck = 0x4
    ChargeStationStatus = 0x10
    ChargeStationAlarm = 0x11
    ChargeStationTask = 0x12
    SensorMonitor = 0x40


class ApiInfo(BaseModel):
    url: str = Field(default='', description='api 接口地址')
    app_id: str = Field(default='com.huawei.me.rcs.servermanage', description='认证 id')
    app_key: str = Field(default='', description='认证密钥')
    topic: str = Field(default='T_LEM_MQ', description='消息主题')
    verify: bool = Field(default=True, description='是否强制 ssl 证书校验')


class ReporterConfig(BaseModel):
    api_info: ApiInfo

    max_retries: int = 3
    retry_wait_base: float = 1.1


class ReportServiceConfig(BaseModel):
    enable: bool = Field(default=True)
    api_info: ApiInfo = Field(default_factory=ApiInfo)
    deploy: DeployInfo = Field(default_factory=DeployInfo)
    tweak: TweakSettings = Field(default_factory=TweakSettings)


class ReportTaskSpec(BaseModel):
    """
    任务详细属性，所有可能需要的属性字段从这里传递
    非必要字段默认留空，使用时仅传递所需字段
    """

    agv_id: int = Field(default=0, description='小车编号')
    map_code: str = Field(default='', description='地图编号')
    carrier_code: str = Field(default='', description='载具编号')
    command_id: str = Field(default='', description='点检任务编号')
    check_action: AutoCheckAction = Field(default=AutoCheckAction.Init, description='车体动作')
    check_type: AutoCheckType = Field(default=AutoCheckType.Vibration_g1, description='点检类型')
    check_result: AutoCheckResult = Field(default=AutoCheckResult.Ok, description='点检结果')
    err_msg: str = Field(default='', description='异常信息')

    guid: Optional[UUID] = Field(
        default=None, description='唯一码，区别于 reqCode, 关联多个独立上报消息'
    )
    uniformID: int = Field(default=0, description='上报任务归一化 ID，由此进行过滤去重检测')
    count_send: int = Field(default=0, description='spec 绑定的上报计数')

    alarmData: Optional[AlarmData] = Field(default=None, description='告警任务可预填写部分告警信息')
    checkDatas: Optional[List[AutoCheckData]] = Field(
        default=None, description='点检任务可预填写的信息'
    )

    upload_img: bool = Field(default=False, description='是否需要扫码上传图片')
    end_on_collect: bool = Field(default=False, description='采集数据时填充结束时间，主动结束')
    end_at_timestamp: float = Field(default=0, description='指定上报结束时间，主动结束')
    delay_ms: int = Field(default=0, description='延迟上报，仅对未设任务启动时间的有效')


class ReportTask(BaseModel):
    reporter_type: ReportType  # 上报类型
    spec: ReportTaskSpec  # 通用的相关信息对象

    req_info: Optional[BaseReqInfo] = None  # 任务请求信息
    enable_debug: bool = True  # 是否启用调试信息

    name: str = ''  # 任务名称
    id: Optional[UUID] = None  # 任务 ID
    interval_ms: int = 200  # 上报周期，单位：毫秒
    max_count: int = 0  # 最大上报次数，0 表示不限次数
    start_time: Optional[float] = None  # 起始上报时间，单位 s, 时间戳 (loop.time())
    end_time: Optional[float] = None  # 结束上报时间，单位 s, 时间戳 (loop.time())
    callback: Optional[Callable] = None  # 周期采集数据的回调函数

    @property
    def desc(self) -> str:
        return f'{self.name}({self.id})'
