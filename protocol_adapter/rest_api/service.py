import asyncio
import logging
import uvicorn

from typing import Optional
from fastapi import FastAPI

from protocol_adapter.utils import MiscUtils
from protocol_adapter.rest_api.settings import ApiSettings, ApiSettingsManager, HealthState
from protocol_adapter.rest_api.settings import SensorThresholdsConfig

logger = logging.getLogger(__name__)


api = FastAPI(
    title='LEM settings api',
    prefix='/api',
    docs_url='/api/docs',
    redoc_url='/api/redoc',
    openapi_url='/api/openapi.json',
)


@api.get('/health', response_model=HealthState, response_model_exclude_none=True)
async def health() -> HealthState:
    return HealthState()


@api.get('/sensorThresholds', response_model=SensorThresholdsConfig)
async def get_sensor_thresholds():
    """获取传感器阈值配置"""
    return ApiSettingsManager().settings.sensor_thresholds


@api.post('/sensorThresholds', response_model=SensorThresholdsConfig)
async def set_sensor_thresholds(config: SensorThresholdsConfig):
    """设置传感器阈值配置"""
    ApiSettingsManager().settings.sensor_thresholds = config
    return ApiSettingsManager().settings.sensor_thresholds


@MiscUtils.singleton
class RestAPI:
    api: FastAPI = api

    def __init__(self, settings: ApiSettings):
        self.api_server: Optional[uvicorn.Server] = None
        ApiSettingsManager().settings = settings

    async def stop(self):
        if self.api_server:
            await self.api_server.shutdown()
            self.api_server = None

    async def serve(self):
        logger.info('serve api ..')

        settings = ApiSettingsManager().settings

        config = uvicorn.Config(
            self.api,
            host=settings.server_config.host,
            port=settings.server_config.port,
            server_header=False,
        )
        self.api_server = uvicorn.Server(config)
        assert self.api_server

        try:
            await self.api_server.serve()
        except asyncio.CancelledError:
            logger.info('api service cancelled')


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    service = RestAPI(ApiSettings())
    asyncio.run(service.serve())
