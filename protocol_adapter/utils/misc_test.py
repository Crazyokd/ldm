# ruff: noqa: PLR2004

import threading
import time

from protocol_adapter.utils.misc import MiscUtils


class TestMiscUtils:
    def test_singleton(self):
        @MiscUtils.singleton
        class Abc:
            a: int
            b: str
            c: list

        obj1 = Abc()
        obj2 = Abc()
        assert obj1 is obj2

    def test_singleton_with_args(self):
        @MiscUtils.singleton(respect_args=True)
        class Abcd:
            def __init__(self, a=0, b=1):
                a += b

        obj1 = Abcd()
        obj2 = Abcd()
        obj3 = Abcd(a=0)
        obj4 = Abcd(a=1)
        obj5 = Abcd(a=1)
        obj6 = Abcd(a=1, b=2)
        obj7 = Abcd(b=2, a=1)

        assert obj1 is obj2  # 默认传参，相同实例
        assert obj2 is not obj3  # 虽然与默认参数相同，但形式传参不同（考虑以元类单例优化）
        assert obj3 is not obj4  # 参数不同，不同实例
        assert obj4 is obj5  # 传参相同，相同实例
        assert obj5 is not obj6  # 传参不同，不同实例
        assert obj6 is obj7  # 传参顺序不影响

    def test_skip_if_running(self):
        @MiscUtils.skip_if_running
        def test_func():
            time.sleep(0.1)
            return 'done'

        results = []

        # 创建两个线程同时调用函数
        def worker():
            results.append(test_func())

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # 验证只有一个调用真正执行了函数
        assert 'done' in results
        assert None in results
        assert len(results) == 2

    def test_skip_if_running_sequential_calls(self):
        call_count = 0

        @MiscUtils.skip_if_running
        def test_func():
            nonlocal call_count
            call_count += 1
            return call_count

        # 顺序调用
        assert test_func() == 1
        assert test_func() == 2
        assert call_count == 2

    def test_run_cmd(self):
        p = MiscUtils.run_cmd('echo abc')
        p.wait()
        assert p.returncode == 0

        p = MiscUtils.run_cmd('sleep 0.1', wait=True)
        assert p.returncode == 0
