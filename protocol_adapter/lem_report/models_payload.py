from dataclasses import field
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer
from typing import List, Dict, Optional


class DeployInfo(BaseModel):
    siteId: str = Field(default='TC06', description='工厂区域, 如: TC06', max_length=64)
    warehouseCode: str = Field(default='T', description='仓库代码, 如: T', max_length=64)
    sourceName: str = Field(default='STD', description='来源系统名称，如: STD', max_length=64)


class BaseReqInfo(DeployInfo):
    # 请求时实时生成
    reqCode: Optional[UUID] = Field(default=None, description='请求编号，每个请求编号唯一')
    reqTime: Optional[datetime] = Field(default=None, description='请求时间')
    operatorNo: str = Field(default='admin', description='操作人工号', max_length=32)

    @field_serializer('reqCode')
    def serialize_guid(self, guid: Optional[UUID]):
        return str(guid) if guid else ''

    @field_serializer('reqTime')
    def serialize_time(self, ts: Optional[datetime]):
        return ts.strftime('%Y-%m-%d %H:%M:%S') if ts else ''


class StatusData(BaseModel):
    deviceCode: str = Field(..., description='设备编号')
    status: int = Field(..., description='设备状态')
    currentX: float = Field(..., description='X坐标')
    currentY: float = Field(..., description='Y坐标')
    currentH: float = Field(..., description='H坐标')
    currentSpeed: float = Field(..., description='当前速度')
    batteryLevel: int = Field(..., description='当前电量')


class AlarmData(BaseModel):
    alarmModule: str = Field(
        default='1', description='报警模块编号(1:设备, 2:服务）)', max_length=32
    )
    mainTypeCode: str = Field(default='0', description='告警主类型', max_length=32)
    minorTypeCode: str = Field(default='0', description='告警子类型', max_length=32)

    deviceNo: str = Field(default='', description='设备编号', max_length=32)
    mapCode: str = Field(default='', description='地图编号', max_length=32)
    alarmGuid: Optional[UUID] = Field(default=None, description='告警唯一码')

    beginDate: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(), description='告警开始时间'
    )
    endDate: Optional[datetime] = Field(default=None, description='告警结束时间')

    alarmX: float = Field(default=0, description='告警X坐标, mm')
    alarmY: float = Field(default=0, description='告警Y坐标, mm')
    alarmH: float = Field(default=0, description='告警H坐标, mm')

    imageData: str = Field(default='', description='告警相关图像数据')
    parameter1: str = Field(default='', description='告警对应的参数1')
    parameter2: str = Field(default='', description='告警对应的参数2')

    @field_serializer('alarmX', 'alarmY', 'alarmH')
    def serialize_float(self, value: float):
        return str(int(value))  # mm 取整

    @field_serializer('alarmGuid')
    def serialize_guid(self, guid: Optional[UUID]):
        return str(guid) if guid else ''

    @field_serializer('beginDate', 'endDate')
    def serialize_time(self, ts: Optional[datetime]):
        return ts.strftime('%Y-%m-%d %H:%M:%S') if ts else ''


class AlarmModel(BaseReqInfo):
    data: List[AlarmData] = Field(default_factory=list)


class ChargeStationAlarmData(AlarmData):
    agvNo: str = Field('', description='充电桩告警字段')


class ChargeStationStatusData(BaseModel):
    deviceNo: str = Field(..., description='充电桩编号', max_length=32)
    agvNo: str = Field(..., description='非充电状态为空')
    status: int = Field(..., description='0:正常, 1:报警, 2:充电')
    mapCode: str = Field(..., description='地图编号')
    chargingMode: int = Field(..., description='充电模式: 0:自动充电, 1:人工手动, 2:空闲')
    connectorCount: int = Field(..., description='充电头接插次数')
    current: str = Field(..., description='电流 A')
    voltage: str = Field(..., description='电压 V')
    temperature: str = Field(..., description='温度')


class ChargeStationTaskData(BaseModel):
    deviceNo: str = Field(..., description='充电桩编号', max_length=32)
    agvNo: str = Field(..., description='非充电状态为空')
    mapCode: str = Field(..., description='地图编号')
    chargingMode: int = Field(..., description='充电模式: 0:自动充电, 1:人工手动, 2:空闲')
    chargingDuration: str = Field(..., description='此次充电时长 min')
    chargingCapacity: str = Field(..., description='此次充电容量，单位 Ah')
    chargingPower: str = Field(..., description='此次充电电量，单位 kWh')
    chargingStartTime: str = Field(..., description='充电开始时间')
    chargingEndTime: str = Field(..., description='充电结束时间')
    maximumChargingCurrent: str = Field(..., description='此次充电最大电流 A')
    maximumChargingVoltage: str = Field(..., description='此次充电最大电压 V')
    maximumChargingTemperature: str = Field(..., description='此次充电最高温度 ℃')


class ChargeStationAlarmModel(BaseReqInfo):
    data: List[ChargeStationAlarmData] = Field(default_factory=list)


class ChargeStationStatusModel(BaseReqInfo):
    data: List[ChargeStationStatusData] = Field(default_factory=list)


class ChargeStationTaskModel(BaseReqInfo):
    data: List[ChargeStationTaskData] = Field(default_factory=list)


## 点检相关


class VibrationData(BaseModel):
    x: List[float] = field(default_factory=list)
    y: List[float] = field(default_factory=list)
    z: List[float] = field(default_factory=list)

    @field_serializer('x', 'y', 'z')
    def serialize_float(self, values: List[float]):
        return [round(v * 1000, 3) for v in values]  # g 转换成 mg, 保留三位小数


class VibrationDetail(BaseModel):
    action: str = Field(default='agvMove')
    dataFrequency: int = Field(default=10, description='震动数据采集频率')
    vibrationData: VibrationData = Field(default_factory=VibrationData)


def serialize_ts_float(values: Optional[List[Dict[int, float]]], prec=1):
    if not values:
        return None
    new_list = []
    for v in values:
        for ts_us, db in v.items():
            t = datetime.fromtimestamp(ts_us / 1e6)
            t_ = t.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            db_ = round(db, prec)
            new_list.append({t_: db_})
    return new_list


class NoiseDetail(BaseModel):
    action: str = Field(default='agvMove')
    noiseData: List[Dict[int, float]] = Field(default_factory=list)

    @field_serializer('noiseData')
    def serialize_data(self, values: List[Dict[int, float]]):
        return serialize_ts_float(values, prec=1)


class AutoCheckMessage(BaseModel):
    autoCheckResult: int = Field(default=0, description='点检结果，0:正常，1:异常')
    creatTime: datetime = Field(
        default_factory=lambda: datetime.now(), description='点检任务创建时间'
    )
    errMsg: str = Field(default='', description='点检结果异常信息，点检正常时可为空')
    fromCode: str = Field(default='', description='当前采集数据的地码/货位')
    toCode: str = Field(default='', description='当前采集数据的地码/货位')
    processDuration: float = Field(default=0, description='采集过程用时, 单位 s')

    checkDetails: Optional[List] = Field(default=None, description='具体采集信息: vibration, noise')

    # motor only, model_dump(exclude_none=True)
    motorType: Optional[str] = Field(
        default=None, description='电机类型,举升:lift，行驶:propel，转向:steering'
    )
    liftCurrent: Optional[List[Dict[int, float]]] = Field(default=None, description='举升电流')
    liftRpm: Optional[List[Dict[int, float]]] = Field(default=None, description='举升转速')
    liftTemp: Optional[List[Dict[int, float]]] = Field(default=None, description='举升温度')
    leftCurrent: Optional[List[Dict[int, float]]] = Field(default=None, description='电流')
    leftRpm: Optional[List[Dict[int, float]]] = Field(default=None, description='转速')
    leftTemp: Optional[List[Dict[int, float]]] = Field(default=None, description='温度')
    rightCurrent: Optional[List[Dict[int, float]]] = Field(default=None, description='电流')
    rightRpm: Optional[List[Dict[int, float]]] = Field(default=None, description='转速')
    rightTemp: Optional[List[Dict[int, float]]] = Field(default=None, description='温度')

    @field_serializer('creatTime')
    def serialize_time(self, ts: Optional[datetime]):
        return ts.strftime('%Y-%m-%d %H:%M:%S') if ts else ''

    @field_serializer('processDuration')
    def serialize_float(self, value: float):
        return round(value, 3)  # 保留三位小数

    @field_serializer(
        'liftCurrent',
        'leftCurrent',
        'rightCurrent',
        'liftRpm',
        'leftRpm',
        'rightRpm',
    )
    def serialize_data(self, values: Optional[List[Dict[int, float]]]):
        return serialize_ts_float(values, prec=3)

    @field_serializer(
        'liftTemp',
        'leftTemp',
        'rightTemp',
    )
    def serialize_temp(self, values: Optional[List[Dict[int, float]]]):
        return serialize_ts_float(values, prec=1)


class AutoCheckData(BaseModel):
    deviceNo: str = Field(default='', description='设备编号', max_length=32)
    mapCode: str = Field(default='', description='地图编号', max_length=32)
    checkType: str = Field(default='', description='点检类型')
    commandId: str = Field(default='', description='点检任务编号')
    message: AutoCheckMessage = Field(default_factory=AutoCheckMessage)


class AutoCheckModel(BaseReqInfo):
    data: List[AutoCheckData] = Field(default_factory=list)
