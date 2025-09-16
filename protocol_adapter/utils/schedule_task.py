import asyncio
import logging

from typing import Optional


_logger = logging.getLogger(__name__)


class ScheduleTask:
    def __init__(self, coro, interval_ms: int, count=0, coro_end=None):
        """
        初始化周期任务类
        :param coro: 周期执行的协程
        :param interval_ms: 执行间隔（毫秒）
        :param count: 执行次数，0 表示无限循环，>0 表示执行指定次数
        :param coro_end: 周期任务正常结束后需要执行的协程
        """
        self._coro = coro
        self._count = count
        self._interval_ms = interval_ms
        self._coro_end = coro_end

        self._task = None
        self._loop = None
        self._running = False

    async def _task_loop(self):
        if not self._running:
            return

        ct = 0
        while self._running:
            if self._count > 0:
                ct += 1
                if ct > self._count:
                    break

            try:
                await self._coro()
            except Exception as e:
                _logger.warning(f'loop task exception: {e}')

            # 执行完等待，只保证执行间隔
            await asyncio.sleep(self._interval_ms / 1000)

        # 执行次数正常完成后进入，stop 取消后不会进到这里
        self._running = False
        self._task = None

        # 执行任务
        if self._coro_end:
            _logger.info('call coro_end() on finished')
            await self._coro_end()

    def is_running(self):
        return self._running

    def start(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is None and self._loop:
            loop = self._loop
        if not loop:
            _logger.warning('skip start: no loop')
            return

        def start_task():
            if not self._running:
                self._running = True
                self._loop = loop
                self._task = loop.create_task(self._task_loop())

        loop.call_soon_threadsafe(start_task)

    def stop(self, *, cancel=True):
        if not self._running:
            return
        self._running = False

        if cancel and self._loop and self._task:
            self._loop.call_soon_threadsafe(self._task.cancel)

    def restart(self):
        if self._loop:
            self.stop()
            self.start()
        else:
            _logger.warning('skip restart: not started!')
