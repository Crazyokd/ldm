import pytest
import asyncio
import threading
import logging

logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)


def pytest_addoption(parser):
    parser.addoption(
        '-E',
        action='store',
        metavar='NAME',
        help='only run tests matching the environment NAME.',
    )


def pytest_configure(config):
    config.addinivalue_line('markers', 'env(name): mark test to run only on named environment')


def pytest_runtest_setup(item):
    envnames = [mark.args[0] for mark in item.iter_markers(name='env')]
    if envnames and item.config.getoption('-E') not in envnames:
        pytest.skip(f'test requires env in {envnames}')


@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    from protocol_adapter.utils import SrosLog

    sros_log = SrosLog('ldm_protocol_adapter')
    sros_log.sendLogToConsole()


@pytest.fixture(scope='session')
def mock_api_server():
    from protocol_adapter.mock.rest_api_mock import ApiManager, ApiConfig

    # NOTE: 注意服务端口与客户端配置同步: main.yaml, report_service_test.py
    config = ApiConfig(port=4097)
    api = ApiManager(config)

    async def stop_api():
        await api.stop()
        # 还需要主动取消任务
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.close()

    def run_api_server(loop):
        """在后台线程中运行事件循环"""
        asyncio.set_event_loop(loop)

        loop.run_until_complete(api.serve())

    # setup: 创建一个新的事件循环并在后台线程中运行
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=run_api_server, args=(loop,), name='mock_api')
    thread.start()

    # 返回执行测试单元
    yield config

    # teardown: 停止事件循环
    asyncio.run_coroutine_threadsafe(stop_api(), loop)
    thread.join(timeout=1)  # 等待线程结束
