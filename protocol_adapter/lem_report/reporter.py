import abc
from uuid import UUID
import httpx
import asyncio
import logging
import pathlib
import base64
import re

from datetime import datetime
from typing import Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor

from protocol_adapter.utils import SnowflakeGenerator
from protocol_adapter.lem_report.models import (
    ApiInfo,
    PayloadType,
    ReportPayload,
    ControlState,
    ReporterConfig,
    ReportTask,
)

logger = logging.getLogger(__name__)


class BaseReporterUtils(abc.ABC):
    config: ReporterConfig
    task: ReportTask
    id_generator: SnowflakeGenerator
    _loop: Optional[asyncio.AbstractEventLoop]

    def gen_req_code(self) -> UUID:
        return self.id_generator.gen_uuid()

    def get_cur_time(self) -> datetime:
        """返回系统时间"""
        return datetime.now()

    def get_loop_ts(self) -> float:
        """返回协程事件循环的稳定单调时间"""
        return self._loop.time() if self._loop else 0

    def encode_image(self, path: pathlib.Path) -> str:
        return base64.b64encode(path.read_bytes()).decode()

    def find_image_around_the_time(
        self,
        ts: Optional[datetime] = None,
        before: float = 2,
        after: float = 0.5,
        directory: str = '',
    ) -> Optional[pathlib.Path]:
        """在指定目录下搜索目标时间前后时段内最邻近的文件"""

        path_dir = pathlib.Path(directory)
        if not (directory and path_dir.exists()):
            logger.warning(f'unkown directory: {directory}')
            return None

        # path: /sros/log/data/dm_svc_failure_2024-12-27-8-57-54.361.day_10.png
        pattern = re.compile(r'(\d{4}' + r'-\d{1,2}' * 5 + r'.\d{1,3})')
        file_ts_fmt = '%Y-%m-%d-%H-%M-%S.%f'
        wildcard = '*.png'

        target_filename = None
        target_ts_delta = None

        if ts is None:
            ts = datetime.now()

        for filename in pathlib.Path(directory).glob(wildcard):
            match = pattern.search(filename.name)
            if match:
                file_ts_str = match.group(1)
                file_ts = datetime.strptime(file_ts_str, file_ts_fmt)
                ts_delta = (ts - file_ts).total_seconds()
                if -after <= ts_delta <= before and (
                    target_ts_delta is None or abs(target_ts_delta) > abs(ts_delta)
                ):
                    target_filename = filename
                    target_ts_delta = ts_delta

        return target_filename

    @staticmethod
    def from_task(
        task: ReportTask,
        executor: ThreadPoolExecutor,
        api_info: ApiInfo,
        on_stop: Optional[Callable[[UUID], None]] = None,
    ) -> Optional['BaseReporter']:
        from protocol_adapter.lem_report.reporters import MAP_REPORTER_TYPE_TO_CLASS

        if task.reporter_type not in MAP_REPORTER_TYPE_TO_CLASS:
            logger.error(f'unknown reporter type: {task.reporter_type}')
            return None

        return MAP_REPORTER_TYPE_TO_CLASS[task.reporter_type](
            task=task,
            executor=executor,
            config=ReporterConfig(api_info=api_info),
            on_stop=on_stop,
        )


class BaseReporterSender(abc.ABC):
    MSG_TAG: str  # 消息类型标签

    config: ReporterConfig
    task: ReportTask

    _api: Optional[httpx.AsyncClient]

    async def send_payload_http(self, data: dict):
        if not self._api:
            self._api = httpx.AsyncClient(verify=self.config.api_info.verify)

        api_info = self.config.api_info
        response = await self._api.post(
            api_info.url,
            json=data,
            headers={
                'X-HW-ID': api_info.app_id,
                'X-HW-APPKEY': api_info.app_key,
                'MsgTopic': api_info.topic,
                'MsgTag': self.MSG_TAG,
                'MsgBusinessId': str(self.task.spec.agv_id),
                'Content-Type': 'application/json',
                'user-agent': '',
            },
        )

        # TODO(zZ): debug only
        logger.warning(f'req header: {response.request.headers}')
        logger.warning(f'req payload: {data}')
        logger.warning(f'resp header: {response.headers}')
        logger.warning(f'resp body: {response.content}')

        try:
            response.raise_for_status()
            ret = response.json()
        except Exception as e:
            logger.error(f'failed on post: {e}')
            ret = {}

        return ret

    async def send_payload_udp(self):
        raise NotImplementedError


class BaseReporter(BaseReporterUtils, BaseReporterSender):
    MSG_TAG: str  # 消息类型标签

    def __init__(
        self,
        config: ReporterConfig,
        task: ReportTask,
        executor: ThreadPoolExecutor,
        on_stop: Optional[Callable[[UUID], None]] = None,
    ):
        self.config = config  # 上报任务的默认配置
        self.task = task  # 上报任务对应的 task 描述
        self.executor = executor  # 执行上报数据采集的 线程池
        self.id_generator = SnowflakeGenerator(node_id=self.task.spec.agv_id)

        self._on_stop = on_stop  # 停止时的回调，接受一个 uuid 传参
        self._running = False  # 运行状态
        self._resume = None  # 等待恢复信号: None -> Event().wait() -> Event().set() -> None
        self._count = 0  # 执行周期计数
        self._fail_ct = 0  # 连续失败计数
        self._api = None  # api 处理对象(http client)
        self._loop = None  # 记录 run() 所在事件循环

    @property
    def name(self):
        return self.task.name

    @property
    def uuid(self):
        return self.task.id

    @property
    def desc(self):
        return self.task.desc

    @property
    def count(self):
        return self._count

    def pause(self):
        logger.info(f'pause task {self.desc}..')
        if not self._resume:
            self._resume = asyncio.Event()

    def resume(self):
        logger.info(f'resume task {self.desc}..')
        if self._resume:
            self._resume.set()

    def stop(self):
        logger.info(f'stop task {self.desc}..')
        self._running = False

        if self._on_stop and self.uuid:
            self._on_stop(self.uuid)

    def reload(self, task: ReportTask):
        logger.info(f'reload task: {self.desc}..')

        # 继承起始时间及 alarmGuid
        if self.task.start_time:
            task.start_time = self.task.start_time
        if task.spec.alarmData and self.task.spec.alarmData:
            task.spec.alarmData.beginDate = self.task.spec.alarmData.beginDate
            task.spec.alarmData.alarmGuid = self.task.spec.alarmData.alarmGuid

        self.task = task

    async def run(self):
        """执行上报任务的周期循环"""
        self._running = True
        self._loop = asyncio.get_running_loop()

        while self._running:
            if self._resume:
                logger.warning(f'task {self.desc} paused, wait resume ..')
                await self._resume.wait()
                self._resume = None
                continue  # 重新检查，万一暂停期间停止任务了呢

            # 检查时间限制
            cur_time = self._loop.time()
            if (self.task.end_time and cur_time > self.task.end_time) or (
                self.task.max_count and self._count >= self.task.max_count
            ):
                self.stop()
                break

            # 执行上报
            if not self.task.start_time or cur_time > self.task.start_time:
                if self.task.enable_debug:
                    logger.debug(f'{self.desc}: send ct={self._count} ..')

                try:
                    payload = await self.get_payload()
                    await self._send_payload(payload)
                    self._fail_ct = 0
                except Exception as e:
                    logger.error(f'{self.desc}: report failed: {e}', exc_info=True)
                    self._fail_ct += 1

                if self._fail_ct > self.config.max_retries:
                    logger.warning(f'stop after max retry failed, tried x{self._fail_ct}')
                    self.stop()
                    break

            # 等待下一个周期
            await asyncio.sleep(self.task.interval_ms / 1000)

    async def get_payload(self) -> ReportPayload:
        """采集构建上报数据，可以通过调整载荷状态改变当前任务行为"""

        def collect_and_build_payload() -> ReportPayload:
            data = self._collect_data()
            return self._build_payload(data)

        assert self._loop
        return await self._loop.run_in_executor(self.executor, collect_and_build_payload)

    @abc.abstractmethod
    def _collect_data(self) -> Any:
        """采集上报信息: 调用上报任务传递的回调，自定义采集逻辑"""
        if not self.task.callback:
            return {}
        return self.task.callback()

    @abc.abstractmethod
    def _build_payload(self, data: Any) -> ReportPayload:
        """构建上报数据: 根据采集数据，生成上报载荷"""
        return ReportPayload()

    async def _send_payload(self, payload: ReportPayload):
        """发送API请求，根据拿到的载荷反馈，调整任务行为"""
        if not payload.skip:
            send_methods = {
                PayloadType.Http: self.send_payload_http,
                PayloadType.Udp: self.send_payload_udp,
            }
            if payload.type in send_methods:
                await send_methods[payload.type](payload.value)
                self._count += 1
                self.task.spec.count_send += 1
            else:
                logger.warning(f'unknown payload type: {payload.type}')

        if payload.state == ControlState.Pause:
            self.pause()
        elif payload.state == ControlState.Stop:
            self.stop()
