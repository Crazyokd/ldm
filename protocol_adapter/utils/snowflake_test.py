import time
import threading
import uuid
import pytest

from typing import Callable

from protocol_adapter.utils import SnowflakeGenerator


class TestSnowflakeGenerator:
    @pytest.fixture(scope='function')
    def generator(self):
        return SnowflakeGenerator(0xABCDE)

    def test_normal_generation(self, generator: SnowflakeGenerator):
        """测试正常生成 ID"""

        print(generator.gen_id())
        print(generator.gen_uuid())

        # 连续循环生成
        id0 = 0
        for _ in range(20):
            id1 = generator.gen_id()
            assert id0 != id1, '生成的 ID 应该唯一'
            id0 = id1

        # 无缝生成
        id1 = generator.gen_id()
        id2 = generator.gen_id()
        assert id1 != id2, '无缝连续生成的 ID 也需唯一'

    def test_clock_rollback(self, generator: SnowflakeGenerator):
        """测试时间回拨"""
        id1 = generator.gen_id()
        # 模拟时间回拨，把记录的时间设到未来时间
        generator.last_ts = int(time.time() * 1000) + 200
        id2 = generator.gen_id()
        assert id1 < id2, '时间回拨后生成的 ID 应该更大'

    def test_concurrent_generation(self, generator: SnowflakeGenerator):
        """测试多线程并发生成 ID"""
        threads = []
        results = set()

        def worker():
            snowflake_id = generator.gen_id()
            results.add(snowflake_id)

        # 创建 20 个线程并发生成 ID
        for _ in range(20):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 检查是否有重复 ID
        assert len(results) == 20, '所有生成的 ID 应该唯一'  # noqa: PLR2004

    @pytest.mark.skip(reason='skip benchmark')
    def test_bench_generator(self, generator: SnowflakeGenerator):
        """性能测试"""

        def bench_gen(name: str, generator: Callable, run_time=4):
            print(f'> bench {name} generator for {run_time}s ..')
            mark = time.time()
            ct = 0
            while True:
                _ = generator()
                ct += 1
                if time.time() - mark > run_time:
                    break
            print(f'. {name} OPS: {ct // run_time} ({run_time}s)')

        # 雪花算法测试
        for run_time in range(2, 4):
            bench_gen('snowflake', generator.gen_id, run_time)

        # uuid4 对照测试
        for run_time in range(2, 4):
            bench_gen('uuid4', uuid.uuid4, run_time)
