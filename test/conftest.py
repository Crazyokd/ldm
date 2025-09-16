import pytest
import logging

_logger = logging.getLogger(__name__)


@pytest.fixture(scope='session', autouse=True)
def test_require_mock_api_server(mock_api_server):
    """通过 pytest 引入 fixture 依赖自动运行 mock api server"""
    _logger.debug(f'mock api server: {mock_api_server}')
