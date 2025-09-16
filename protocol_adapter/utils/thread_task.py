import logging
import time
import threading

from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ThreadTask:
    def __init__(
        self,
        on_retry: Callable,
        on_success: Optional[Callable] = None,
        retry_interval: float = 1,
        max_try: int = 0,
        name: str = '',
    ):
        self._on_retry = on_retry
        self._on_success = on_success
        self._retry_interval = retry_interval
        self._retry_count_max = max_try
        self._name = name

        self._stopped: Optional[threading.Event] = None

    def start(self, delay: float = 0):
        # 如果已经启动，先把前一次的任务停掉
        if self._stopped:
            self._stopped.set()

        self._stopped = threading.Event()

        def retry_in_thread(stopped: threading.Event):
            if delay > 0:
                time.sleep(delay)

            ct = 0
            while not stopped.is_set() and not self._on_retry():
                ct += 1
                if self._retry_count_max > 0 and ct >= self._retry_count_max:
                    stopped.set()
                    break
                logger.warning(f'failed on try {ct}, retry after {self._retry_interval}s ..')
                time.sleep(self._retry_interval)

            if not stopped.is_set() and self._on_success:
                self._on_success()

            logger.debug(f'retry end, fail x{ct}')

        t = threading.Thread(
            target=retry_in_thread, args=(self._stopped,), name=self._name, daemon=True
        )
        t.start()

    def stop(self):
        if self._stopped and not self._stopped.is_set():
            self._stopped.set()
