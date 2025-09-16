#!/usr/bin/env python3

import asyncio
from enum import Enum


class AsyncResultState(Enum):
    """结果状态枚举"""

    NONE = 0
    ACCEPT = 1
    REJECT = 2


class AsyncResult:
    """
    异步等待结果,支持多线程中设置结果

    注意线程安全：
    1. 此对象应当在 loop 绑定的线程中创建
    2. clear(), wait() 只能在 loop 所属线程调用
    """

    def __init__(self, loop):
        self._loop = loop

        # 注意：event 与当前线程的事件循环绑定，初始化时应当运行于 loop 所在线程
        self._event = asyncio.Event()

        self._result = None
        self._result_dat = None  # 结果数据
        self._result_state = AsyncResultState.NONE

    def get_result(self):
        return self._result

    def get_result_dat(self):
        return self._result_dat

    def clear(self):
        self._event.clear()
        self._result = None
        self._result_dat = None
        self._result_state = AsyncResultState.NONE

    async def wait(self):
        await self._event.wait()
        if self._result_state is None:
            raise Exception('UNREACHABLE')
        elif self._result_state == AsyncResultState.ACCEPT:
            return self._result
        else:
            raise RuntimeError('sync request reject, error code: ', self._result)

    def reject(self, result=None):
        def fun(self):
            self._result_state = AsyncResultState.REJECT
            self._result = result
            self._event.set()

        self._loop.call_soon_threadsafe(fun, self)

    def accept(self, result=None, dat=None):
        def fun(self):
            self._result_state = AsyncResultState.ACCEPT
            self._result_dat = dat
            self._result = result
            self._event.set()

        self._loop.call_soon_threadsafe(fun, self)


if __name__ == '__main__':
    import threading
    import time

    loop = asyncio.new_event_loop()
    async_result = AsyncResult(loop)

    async def action(async_result):
        async_result.clear()
        # do something
        print('wait result: ', threading.current_thread())
        return await async_result.wait()

    def new_result(async_result):
        time.sleep(1)
        async_result.accept(100)
        print('new result 100: ', threading.current_thread())

    f = action(async_result)
    # loop.call_later(1, new_result, async_result) # result fun call in the same thread
    threading.Thread(
        target=new_result, args=(async_result,)
    ).start()  # result call in different thread
    loop.run_until_complete(f)
    loop.close()
    time.sleep(0.1)
    print(async_result.get_result(), threading.current_thread())
