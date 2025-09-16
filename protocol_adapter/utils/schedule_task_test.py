import asyncio
import threading
import time

import pytest
import pytest_mock

from protocol_adapter.utils.schedule_task import ScheduleTask


class TestScheduleTask:
    loop: asyncio.AbstractEventLoop

    @pytest.fixture(scope='function', autouse=True)
    def up_and_down(self):
        """fixture as setup/teardown method for the test unit"""

        def _run_loop(event: threading.Event):
            """在后台线程中运行事件循环"""
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            event.set()

            try:
                self.loop.run_forever()
            finally:
                for task in asyncio.all_tasks(self.loop):
                    task.cancel()
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
                self.loop.close()

        # setup: 创建一个新的事件循环并在后台线程中运行
        ready = threading.Event()
        thread = threading.Thread(target=_run_loop, args=[ready])
        thread.start()
        ready.wait()

        # 返回执行测试单元
        yield

        # teardown: 停止事件循环
        self.loop.call_soon_threadsafe(self.loop.stop)
        thread.join(timeout=1)  # 等待线程结束

    def test_start_stop_and_loop(self, mocker: pytest_mock.MockerFixture):
        """测试任务的启动和停止"""
        mock_coro = mocker.AsyncMock()
        task = ScheduleTask(mock_coro, interval_ms=100)

        # 启动任务
        task.start(self.loop)
        time.sleep(0.3)

        assert task.is_running()
        assert mock_coro.call_count > 1

        # 停止任务
        task.stop()
        time.sleep(0.1)
        assert not task.is_running()

    def test_task_count(self, mocker: pytest_mock.MockerFixture):
        """测试任务执行次数"""
        mock_coro = mocker.AsyncMock()
        mock_coro_end = mocker.AsyncMock()
        task = ScheduleTask(mock_coro, interval_ms=50, count=4, coro_end=mock_coro_end)

        # 启动任务
        task.start(self.loop)
        time.sleep(0.4)

        # 任务应该已经自动停止
        assert not task.is_running()

        # 验证协程被调用了指定次数
        assert mock_coro.call_count == 4  # noqa: PLR2004
        assert mock_coro_end.call_count == 1

        # 重启任务，提前停止，不会调 coro_end
        task.restart()

        time.sleep(0.1)
        task.stop()

        assert mock_coro.call_count > 4  # noqa: PLR2004
        assert mock_coro_end.call_count == 1

    def test_task_exception(self, mocker: pytest_mock.MockerFixture):
        """测试任务异常处理"""
        mock_coro = mocker.AsyncMock(side_effect=Exception('Test Exception'))
        task = ScheduleTask(mock_coro, interval_ms=50, count=4)

        # 启动任务
        task.start(self.loop)
        time.sleep(0.5)

        # 验证协程被调用了多次，即使有异常
        assert mock_coro.call_count == 4  # noqa: PLR2004
        assert not task.is_running()

    def test_task_restart(self, mocker: pytest_mock.MockerFixture):
        """测试任务重启"""
        mock_coro = mocker.AsyncMock()
        task = ScheduleTask(mock_coro, interval_ms=50)

        # 任务未启动过，重启任务无效
        task.restart()
        time.sleep(0.1)
        assert not task.is_running()

        # 启动任务
        task.start(self.loop)
        time.sleep(0.1)
        assert task.is_running()

        # 停止任务
        task.stop()
        time.sleep(0.1)
        assert not task.is_running()

        # 重启任务: 重启有效
        task.restart()
        time.sleep(0.1)
        assert task.is_running()

        # 停止任务，留点时间给协程执行退出
        task.stop()
        assert not task.is_running()

    def test_task_end_on_stop(self, mocker: pytest_mock.MockerFixture):
        """测试携程任务结束后不再执行"""
        mock_coro = mocker.AsyncMock()
        task = ScheduleTask(mock_coro, interval_ms=50)

        # 启动任务
        task.start(self.loop)
        time.sleep(0.1)
        assert task.is_running()

        # 停止任务
        task.stop()
        time.sleep(0.1)
        assert not task.is_running()

        # 任务停止后，不应再有执行
        run_ct = mock_coro.call_count
        time.sleep(0.4)
        assert run_ct == mock_coro.call_count
