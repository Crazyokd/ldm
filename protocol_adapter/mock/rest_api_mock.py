import asyncio
import logging
import uvicorn

from typing import Optional
from pydantic import Field, BaseModel
from fastapi import FastAPI, Request

from protocol_adapter.utils import MiscUtils

logger = logging.getLogger(__name__)


api = FastAPI(
    title='Mock API',
    prefix='/api',
    docs_url='/api/docs',
    redoc_url='/api/redoc',
    openapi_url='/api/openapi.json',
)


@api.get('/{uri}')
async def echo_get(uri: str, req: Request):
    logger.debug(f'req header: {req.headers}')
    logger.debug(f'req body: {await req.body()}')
    return f'get {uri}:\n{req.headers}'


@api.post('/{uri}')
async def echo_post(uri: str, req: Request):
    logger.debug(f'req header: {req.headers}')
    logger.debug(f'req body: {await req.body()}')
    return await req.body()


class ApiConfig(BaseModel):
    host: str = Field(default='127.0.0.1', description='api 绑定地址')
    port: int = Field(default=4097, description='api 绑定端口', ge=0)
    interface: str = Field(default='abc', description='api 接口地址')
    tls: bool = Field(default=False, description='是否使用 https')
    workers: int = Field(default=1, description='api 工作线程数', gt=0)

    @property
    def url(self):
        prefix = 'https' if self.tls else 'http'
        return f'{prefix}://{self.host}:{self.port}/{self.interface}'


@MiscUtils.singleton
class ApiManager:
    api: FastAPI = api

    def __init__(self, config: ApiConfig):
        self.api_server: Optional[uvicorn.Server] = None
        self.config = config

    async def stop(self):
        if self.api_server:
            await self.api_server.shutdown()

    async def serve(self):
        logger.info('serve api ..')

        config = uvicorn.Config(
            self.api,
            host=self.config.host,
            port=self.config.port,
            workers=self.config.workers,
        )
        self.api_server = uvicorn.Server(config)
        assert self.api_server

        try:
            await self.api_server.serve()
        except asyncio.CancelledError:
            logger.info('api service cancelled')


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    config = ApiConfig()
    manager = ApiManager(config)
    asyncio.run(manager.serve())
