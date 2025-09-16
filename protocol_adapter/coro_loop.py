import asyncio
import threading
import logging

from concurrent.futures import ThreadPoolExecutor

from protocol_adapter.models.settings import TweakSettings

logger = logging.getLogger(__name__)


class AdapterCoroLoop:
    """
    管理其它协程模块启动逻辑

    TODO(any): 原先逻辑大部分基于线程，混杂部分协程，虽然隔离性更好，但使用多有不便；
    对于这种网络通讯和多任务处理，统一使用协程可以简化很多逻辑，提高运行效率，可以考虑重构；
    后续新增的模块，基本上都是新开线程，在线程中运行各自的协程事件循环，多有重复逻辑；
    这里准备统一管理各协程模块入口，简化逻辑
    """

    _executor: ThreadPoolExecutor
    _tweakSettings: TweakSettings = TweakSettings()

    def __init__(self):
        self._loop = None
        self._thread = None
        self._ready = threading.Event()

    def is_ready(self):
        return self._ready.is_set()

    async def set_ready(self):
        self._ready.set()

    def run_coro_loop(self):
        if self._loop is None:
            self._loop = asyncio.new_event_loop()

        # debug if there is any slow coroutine in the loop
        self._loop.set_debug(self._tweakSettings.loop.debug)
        self._loop.slow_callback_duration = self._tweakSettings.loop.slow_ms / 1000

        asyncio.set_event_loop(self._loop)
        self._loop.create_task(self.set_ready())

        try:
            self._loop.run_forever()
        finally:
            self._ready.clear()
            for task in asyncio.all_tasks(self._loop):
                task.cancel()
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.close()
            self._loop = None

    def start(self, *, wait_ready=False):
        if self._loop:
            logger.warning('already running?')
            return

        self._executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix='coro')

        self._thread = threading.Thread(target=self.run_coro_loop, name='ReportService')
        self._thread.start()

        if wait_ready and not self._ready.is_set():
            logger.info('wait coroLoop ready ..')
            self._ready.wait()

        logger.info('coroLoop started')

    def stop(self):
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

        self._executor.shutdown()

        if self._thread:
            self._thread.join()

        logger.info('report service stopped')
