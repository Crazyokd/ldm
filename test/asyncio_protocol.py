import asyncio
import threading
import logging
from functools import wraps

_logger = logging.getLogger(__name__)


class AsyncioProtocol:
    """
    用一个线程来单独处理通信
    """

    _loop: asyncio.AbstractEventLoop

    def __init__(self):
        self._transport = None
        self._protocol = None
        self._sock = None

    def start(self):
        if self._sock is None:
            raise Exception('Please setup sock before!')

        def start_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            th_event.set()
            try:
                loop.run_forever()
            finally:
                for task in asyncio.all_tasks(loop):
                    task.cancel()
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
                if self._sock:
                    self._sock.close()

        th_event = threading.Event()
        t = threading.Thread(target=start_loop, name='AsyncioProtocol')
        t.start()
        th_event.wait()

        asyncio.run_coroutine_threadsafe(self._connect(), self._loop)

    def run_coroutine_threadsafe(func):
        @wraps(func)
        def run(self, *args, **kwargs):
            future = asyncio.run_coroutine_threadsafe(func(self, *args, **kwargs), self._loop)
            try:
                future.result()
            except Exception as e:
                _logger.error(f'Exception occurred: {e}', stack_info=True)

        return run

    @run_coroutine_threadsafe
    async def stop(self):
        if self._loop:
            self._loop.stop()
        if self._transport:
            self._transport.close()

    async def _connect(self):
        raise Exception('Over write this function!')
