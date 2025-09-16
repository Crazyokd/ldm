import time
import pytest
import pytest_mock

from protocol_adapter.utils.thread_task import ThreadTask


@pytest.fixture
def mock_on_retry(mocker: pytest_mock.MockerFixture):
    return mocker.Mock()


@pytest.fixture
def mock_on_success(mocker: pytest_mock.MockerFixture):
    return mocker.Mock()


@pytest.fixture
def thread_task(mock_on_retry, mock_on_success):
    return ThreadTask(
        on_retry=mock_on_retry,
        on_success=mock_on_success,
        retry_interval=0.1,  # 使用较短的间隔以便快速测试
        max_try=8,
        name='test_retry',
    )


def test_thread_task(thread_task, mock_on_retry):
    # 确保在没有启动的情况下调用 stop 不会抛出异常
    thread_task.stop()

    # 模拟 on_retry 始终返回 False，触发重试
    mock_on_retry.return_value = False

    # 等待一段时间以确保线程运行
    thread_task.start()
    time.sleep(0.5)
    thread_task.stop()

    # 确保 on_retry 被调用 1 次以上
    assert mock_on_retry.call_count > 1


def test_thread_task_success(thread_task, mock_on_retry, mock_on_success):
    # 模拟 on_retry 在前两次调用后返回 True
    mock_on_retry.side_effect = [False, False, True]

    thread_task.start()
    time.sleep(0.5)  # 等待一段时间以确保线程运行

    # 确保 on_success 被调用
    assert mock_on_retry.call_count == 3  # noqa: PLR2004
    mock_on_success.assert_called_once()


def test_thread_task_max_retries(thread_task, mock_on_retry, mock_on_success):
    # 模拟 on_retry 始终返回 False，触发最大重试次数
    mock_on_retry.return_value = False

    thread_task.start()
    time.sleep(1)  # 等待一段时间以确保线程运行

    # 确保 on_retry 被调用 max_try 次
    assert mock_on_retry.call_count == thread_task._retry_count_max

    # 确保 on_success 没有被调用
    mock_on_success.assert_not_called()
