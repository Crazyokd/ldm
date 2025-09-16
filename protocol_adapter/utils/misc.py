import logging
import datetime
import threading
import subprocess

from pathlib import Path
from typing import MutableSequence

_logger = logging.getLogger(__name__)

NTP_PORT_STANDARD = 123


class MiscUtils:
    @staticmethod
    def singleton(_cls=None, *, respect_args=False):
        """单例装饰器，支持不同传参创建新的实例

        注意：默认值初始化与传相同值初始化，将生成不同实例(形式传参不同)
        """

        def real_singleton(cls_):
            instances = {}

            def wrapper(*args, **kwargs):
                key = cls_ if not respect_args else (cls_, args, frozenset(kwargs.items()))

                if key not in instances:
                    instances[key] = cls_(*args, **kwargs)
                return instances[key]

            return wrapper

        if _cls is None:
            return real_singleton
        else:
            return real_singleton(_cls)

    @staticmethod
    def skip_if_running(func):
        lock = threading.Lock()

        def wrapper(*args, **kwargs):
            if lock.locked():
                _logger.warning(f'{func.__name__} is running, please try later!')
                return
            with lock:
                return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def append_unique(data: MutableSequence, value):
        if not data or data[-1] != value:
            data.append(value)

    @staticmethod
    def run_cmd(cmd: str, *, wait=False):
        _logger.info(f'run cmd: {cmd}')
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL)
        if wait:
            p.wait()
        return p

    @staticmethod
    def setup_timesyncd(ntp_server: str, port: int, interval_min: int):
        # TODO: 截至 2024.12.23, systemd 不支持传 NTP 服务器端口
        #   华为这边说端口号暂时不会是 123 之外的，先用这个系统服务吧
        if port != NTP_PORT_STANDARD:
            _logger.warning(
                f'provided port({port}) is not the standard {NTP_PORT_STANDARD}, ignore'
            )
            return

        # 保证：16 <= PollIntervalMin < PollIntervalMaxSec
        poll_interval_sec = max(interval_min * 60, 60)
        config_timesyncd = '\n'.join(
            [
                '[Time]',
                f'NTP={ntp_server}',
                'PollIntervalMinSec=32',
                f'PollIntervalMaxSec={poll_interval_sec}',
            ]
        )

        try:
            with Path('/etc/systemd/timesyncd.conf').open('w') as config_file:
                config_file.write(config_timesyncd)
        except Exception as e:
            _logger.error(f'failed to write timesyncd.conf: {e}')
            return

        MiscUtils.run_cmd('systemctl restart systemd-timesyncd')

    @staticmethod
    def set_current_time(timezone: int, time_to_set: int):
        # timezone 没用到，当作 UTC+8
        # MiscUtils.run_cmd('timedatectl set-timezone Asia/Hong_Kong')

        # set-ntp true/false 都会停止 systemd-timesyncd 服务
        MiscUtils.run_cmd('timedatectl set-ntp false')

        time_obj = datetime.datetime.fromtimestamp(time_to_set)
        time_str = time_obj.strftime('%Y-%m-%d %H:%M:%S')
        MiscUtils.run_cmd(f'timedatectl set-time "{time_str}"')
