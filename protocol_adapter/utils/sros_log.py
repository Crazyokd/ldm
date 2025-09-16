#!/usr/bin/env python3

import logging
import logging.handlers

import os
import pathlib

DATE_FMT = '%m%d %H:%M:%S'
LOG_FMT = (
    '%(levelname).1s%(asctime)s.%(msecs)03d %(threadName)-1s '
    '%(filename)-1s:%(lineno)-s] %(message)s'
)


class SrosLog:
    """
    SROS中python进程的日志管理类，所有进程python进程都必须引用此类来生成日志。
    使用方法：
    1.在所有进程开始的地方初始化该类，并调用sendLogToFile()函数
    2.若需要输出到控制台的，手动调用一下sendLogToConsole()函数
    3.所有需要输出日志的类调用如下代码：
        import logging
        _logger = logging.getLogger(__name__)
    4.在需要输出日志的地方插入日志输出，如下代码：
        _logger.info("info: sros log example")
        _logger.error("error： sros log example")
    """

    def __init__(self, module_name):
        """
        初始化sros日志
        :param module_name: 日志的模块名
        """
        self._module_name = module_name

        self._logger = logging.getLogger()
        self._logger.setLevel(logging.NOTSET)

    def sendLogToConsole(self, level=logging.DEBUG):
        """
        将日志打印到控制台，默认不打印
        :param level:
        :return:
        """
        try:
            import colorlog
        except ImportError:
            formatter = logging.Formatter(LOG_FMT, datefmt=DATE_FMT)
        else:
            formatter = colorlog.ColoredFormatter(f'%(log_color)s{LOG_FMT}', datefmt=DATE_FMT)

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(level)
        self._logger.addHandler(handler)

    def sendLogToFile(self, level=logging.INFO, directory='/sros/log/'):
        """
        所有的进程日志都会放到/sros/log/目录下，除了主进程sros外，其他的进程都用进程名的文件夹包裹。
        参见：http://wiki.standard-robots.com/wiki/doku.php?id=project:sros:process_manager
        :param level:
        :return:
        """

        log_dir = pathlib.Path(f'{directory}/{self._module_name}/')
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f'failed to mkdir {log_dir}: {e}')

        if not os.access(log_dir, os.W_OK):
            print(f'skip log to file: no write permission: {log_dir}')
            return

        formatter = logging.Formatter(LOG_FMT, datefmt=DATE_FMT)
        handler = logging.handlers.TimedRotatingFileHandler(
            f'{log_dir}/{self._module_name}.log', when='D', interval=1, backupCount=10
        )
        handler.setLevel(level)
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)


if __name__ == '__main__':
    sros_log = SrosLog('sros_log_example')

    sros_log.sendLogToFile()
    sros_log.sendLogToConsole()

    _logger = logging.getLogger(__name__)

    _logger.info('sros info log example')
    _logger.error('sros error log example')
