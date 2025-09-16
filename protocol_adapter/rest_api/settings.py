from pydantic import BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError

from protocol_adapter.utils.misc import MiscUtils

API_VERSION = '0.1'


class VibrationThreshold(BaseModel):
    """震动传感器阈值配置"""

    warning: float = Field(default=5.0, description='震动告警阈值 g', gt=0, le=10)
    critical: float = Field(default=10.0, description='震动停车阈值 g', gt=0, le=15)

    @model_validator(mode='after')
    def validate_comparison(self):
        if self.critical < self.warning:
            raise PydanticCustomError(
                'invalidThreshold',
                'critical should be greater than warning',
                {},
            )
        return self


class NoiseThreshold(BaseModel):
    """噪音传感器阈值配置"""

    warning: float = Field(default=65.0, description='噪音告警阈值 dB', gt=10, le=100)
    critical: float = Field(default=75.0, description='噪音停车阈值 dB', gt=20, le=128)

    @model_validator(mode='after')
    def validate_comparison(self):
        if self.critical < self.warning:
            raise PydanticCustomError(
                'invalidThreshold',
                'critical should be greater than warning',
                {},
            )
        return self


class LoadUnitThreshold(BaseModel):
    """载荷单元传感器阈值配置"""

    weight_warning: float = Field(default=400.0, description='重量告警阈值 kg', gt=1, le=10000)
    weight_critical: float = Field(default=450.0, description='重量停车阈值 kg', gt=1, le=10000)
    offset_warning: float = Field(default=0.3, description='偏移告警阈值 m', gt=0, le=10)
    offset_critical: float = Field(default=0.5, description='偏移停车阈值 m', gt=0, le=10)
    offset_weight_threshold: float = Field(
        default=5.0, description='需要考虑偏载的最小重量 (kg)', gt=1, le=10000
    )

    @model_validator(mode='after')
    def validate_comparison(self):
        if self.weight_critical < self.weight_warning or self.offset_critical < self.offset_warning:
            raise PydanticCustomError(
                'invalidThreshold',
                'critical should be greater than warning',
                {},
            )
        return self


class MotorThreshold(BaseModel):
    """电机传感器阈值配置"""

    current_warning: float = Field(default=15.0, description='电流告警阈值 A', gt=0, le=1000)
    current_critical: float = Field(default=20.0, description='电流停车阈值 A', gt=0, le=1000)
    temperature_warning: float = Field(default=80.0, description='温度告警阈值 ℃', gt=-50, le=200)
    temperature_critical: float = Field(default=100.0, description='温度停车阈值 ℃', gt=-50, le=200)

    @model_validator(mode='after')
    def validate_comparison(self):
        if (
            self.current_critical < self.current_warning
            or self.temperature_critical < self.temperature_warning
        ):
            raise PydanticCustomError(
                'invalidThreshold',
                'critical should be greater than warning',
                {},
            )
        return self


class SensorThresholdsConfig(BaseModel):
    """所有传感器阈值配置"""

    vibration_1: VibrationThreshold = Field(
        default_factory=VibrationThreshold, description='震动传感器配置'
    )
    noise_1: NoiseThreshold = Field(default_factory=NoiseThreshold, description='噪音传感器阈值')
    loadunit_1: LoadUnitThreshold = Field(
        default_factory=LoadUnitThreshold, description='载荷单元传感器阈值'
    )
    motor_lift: MotorThreshold = Field(default_factory=MotorThreshold, description='举升电机阈值')
    motor_rotate: MotorThreshold = Field(default_factory=MotorThreshold, description='旋转电机阈值')
    motor_left: MotorThreshold = Field(default_factory=MotorThreshold, description='左行走电机阈值')
    motor_right: MotorThreshold = Field(
        default_factory=MotorThreshold, description='右行走电机阈值'
    )


class ServerConfig(BaseModel):
    host: str = Field(default='0.0.0.0', description='api 绑定地址')
    port: int = Field(default=8086, description='api 绑定端口', ge=0)
    tls: bool = Field(default=False, description='是否使用 https')
    interface: str = Field(default='config', description='api 接口地址')

    @property
    def url(self):
        prefix = 'https' if self.tls else 'http'
        return f'{prefix}://{self.host}:{self.port}/{self.interface}'


class HealthState(BaseModel):
    api_ver: str = Field(default=API_VERSION, description='current api version')
    emsg: str = Field(default='', description='error messages if any')


class ApiSettings(BaseModel):
    server_config: ServerConfig = Field(default_factory=ServerConfig)
    sensor_thresholds: SensorThresholdsConfig = Field(default_factory=SensorThresholdsConfig)


@MiscUtils.singleton
class ApiSettingsManager:
    settings = ApiSettings()
