import asyncio
import threading
import logging

from uuid import UUID
from typing import Optional, Dict
from concurrent.futures import ThreadPoolExecutor

from protocol_adapter.utils import SnowflakeGenerator, MiscUtils
from protocol_adapter.lem_report.models import (
    BaseReqInfo,
    ReportServiceConfig,
    ReportTask,
)
from protocol_adapter.lem_report.reporter import BaseReporter

logger = logging.getLogger(__name__)


class ReportServiceBase:
    _task_queue: asyncio.Queue
    _executor: ThreadPoolExecutor

    def __init__(self, config: Optional[ReportServiceConfig] = None):
        self.config = config or ReportServiceConfig()

        self._reporters: Dict[UUID, BaseReporter] = {}
        self._coming_tasks: Dict[int, UUID] = {}  # 需要去重的待添加任务(未进 _reporters)

        self._loop = None
        self._thread = None
        self._ready = threading.Event()

    def is_ready(self):
        return self._ready.is_set()

    def get_loop_ts(self) -> float:
        if not self._loop:
            logger.warning('service not ready on get_loop_ts()')
            return 0
        return self._loop.time()

    def service_loop(self):
        if self._loop is None:
            self._loop = asyncio.new_event_loop()

        # debug if there is any slow coroutine in the loop
        self._loop.set_debug(self.config.tweak.loop.debug)
        self._loop.slow_callback_duration = self.config.tweak.loop.slow_ms / 1000

        asyncio.set_event_loop(self._loop)
        self._loop.create_task(self.process_task_queue())
        self._ready.set()

        try:
            self._loop.run_forever()
        finally:
            self._ready.clear()
            for task in asyncio.all_tasks(self._loop):
                task.cancel()
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.close()
            self._loop = None

    async def process_task_queue(self):
        """处理上报任务队列"""

        # 事件循环内创建队列
        self._task_queue = asyncio.Queue(maxsize=self.config.tweak.report.queue_size)

        while self._loop:
            # 等待新的上报任务
            task = await self._task_queue.get()

            # 实例化新的 reporter 或者更新已有 reporter
            if task.id in self._reporters:
                self._reporters[task.id].reload(task)
            else:
                # 通过回调删结束后的任务，字典删改操作都在线程内
                def on_stop(task_id: UUID):
                    self._reporters.pop(task_id)

                reporter = BaseReporter.from_task(
                    task,
                    self._executor,
                    self.config.api_info,
                    on_stop=on_stop,
                )
                if reporter:
                    self._reporters[task.id] = reporter
                    self._loop.create_task(reporter.run())

                # 处理后从待添加任务中移除
                if task.spec.uniformID in self._coming_tasks:
                    self._coming_tasks.pop(task.spec.uniformID)

            # 通知任务队列执行 +1
            self._task_queue.task_done()

    def start(self, *, wait_ready=False):
        if self._loop:
            logger.warning('already running?')
            return

        self._executor = ThreadPoolExecutor(
            max_workers=self.config.tweak.report.workers, thread_name_prefix='reporter'
        )

        self._thread = threading.Thread(target=self.service_loop, name='ReportService')
        self._thread.start()

        if wait_ready and not self._ready.is_set():
            logger.info('wait servie ready ..')
            self._ready.wait()

        logger.info('report service started')

    def stop(self):
        if self._loop:
            for task_id in list(self._reporters.keys()):
                self.kill_task(task_id)
            self._loop.call_soon_threadsafe(self._loop.stop)

        self._coming_tasks.clear()
        self._executor.shutdown()

        if self._thread:
            self._thread.join()

        logger.info('report service stopped')

    def uniform_coming_task(self, task: ReportTask):
        """新增任务的检查预处理"""
        if not task.id:
            task.id = SnowflakeGenerator(node_id=task.spec.agv_id).gen_uuid()

    def add_task(self, task: ReportTask, *, wait_ready=False) -> Optional[UUID]:
        """添加上报任务

        Args:
            task: 添加到上报服务的任务
            wait_ready: 是否阻塞等待就绪后添加任务
        Return:
            返回添加后的任务 id
        """
        if not self.config.enable:
            logger.warning('servie not enabled')
            return None

        if wait_ready and not self._ready.is_set():
            logger.info('wait servie ready ..')
            self._ready.wait()

        if not self.is_ready() or not self._loop:
            logger.warning('service not ready')
            return None

        self.uniform_coming_task(task)

        async def queue_task():
            if self._task_queue.full():
                logger.warning(f'task queue is full. discarding new task: {task}')
                return ''

            await self._task_queue.put(task)

        logger.info(f'add task: {task.desc}..')
        asyncio.run_coroutine_threadsafe(queue_task(), self._loop)

        return task.id

    def pause_task(self, task_id: UUID):
        """暂停指定 id 的上报任务"""
        if not self._loop:
            return

        reporter = self._reporters.get(task_id)
        if reporter:
            logger.info(f'pause task: {reporter.task.desc}..')
            self._loop.call_soon_threadsafe(reporter.pause)

    def resume_task(self, task_id: UUID):
        """继续指定 id 的上报任务"""
        if not self.is_ready() or not self._loop:
            logger.warning('service not ready, skip resume')
            return

        reporter = self._reporters.get(task_id)
        if reporter:
            logger.info(f'resume task: {reporter.task.desc}..')
            self._loop.call_soon_threadsafe(reporter.resume)

    def kill_task(self, task_id: UUID):
        """停止指定 id 的上报任务"""
        if not self._loop:
            return

        reporter = self._reporters.get(task_id)
        if reporter:
            logger.info(f'kill task: {reporter.task.desc}..')
            self._loop.call_soon_threadsafe(reporter.stop)


@MiscUtils.singleton
class ReportService(ReportServiceBase):
    """涉及业务的实现定制"""

    def uniform_coming_task(self, task: ReportTask):
        """
        统一检查处理待添加的任务：
        1. 从服务的配置信息中同步部署信息到任务(如果任务未特别指明)
        2. 对于部分类型的任务，需要检查已有任务处理合并去重的逻辑
        """
        assert self._loop

        # 任务去重，连续相同 uniformID 的告警，过滤合并成一个任务(赋相同id)
        if not task.id and task.spec.uniformID > 0:
            # 如果已经在待添加任务中了，直接使用对应的 id，以便后续 reload
            if task.spec.uniformID in self._coming_tasks:
                task.id = self._coming_tasks[task.spec.uniformID]
            else:
                # 当前上报任务里面找相同 uniformID 的任务，复用 id
                for task_id, reporter in self._reporters.items():
                    if task.spec.uniformID == reporter.task.spec.uniformID:
                        task.id = task_id
                        break

        # 生成任务 id，如果还没有的话
        if not task.id:
            task.id = SnowflakeGenerator(node_id=task.spec.agv_id).gen_uuid()

        # 还没执行前都去占个位标记下
        if task.spec.uniformID and task.spec.uniformID not in self._coming_tasks:
            self._coming_tasks[task.spec.uniformID] = task.id

        # 默认任务 guid 为任务 id (如果没有另外声明的话)
        if not task.spec.guid:
            task.spec.guid = task.id

        # 使用配置服务的部署信息（来自配置文件）
        if task.req_info is None:
            task.req_info = BaseReqInfo.model_validate(self.config.deploy.model_dump())

        if not task.start_time and task.spec.delay_ms > 0:
            task.start_time = self.get_loop_ts() + task.spec.delay_ms / 1000
