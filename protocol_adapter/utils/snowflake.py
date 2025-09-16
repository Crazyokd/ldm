import time
import threading
import logging
import uuid

from .misc import MiscUtils

logger = logging.getLogger(__name__)


@MiscUtils.singleton(respect_args=True)
class SnowflakeGenerator:
    """
    雪花 id 方案: magic_clk_ts_node_seq_ns

    .  magic(16): 自定义魔法(最好让第一 bit 为0, 符号处理)
    .  rb(4): 时钟回拨次数, 1ms 最多 16 次时光倒流
    .  ts(44): ms 时间戳，大概 557 年
    .  node_id(20): 节点 id, 1048576
    .  seq(28): 每 ms 最大生成 id 数
    .  th_ns(16): 线程 ns 的末 16 bit，当作随机数
    """

    def __init__(self, node_id: int, magic=0x4EC0):
        if node_id < 0 or node_id > 2**20:
            logger.warning(f'node_id({node_id}) not in range: [0, {2**20})')

        self.magic = magic & 0xFFFF
        self.rb = 0
        self.node_id = node_id
        self.seq = 0

        self.last_ts = -1

        self.lock = threading.Lock()

    def gen_id(self) -> int:
        ts_now = lambda: int(time.time() * 1000)

        with self.lock:
            current_ts = ts_now()

            # 处理时间回拨：逻辑时钟自增，物理时间用当前值
            if current_ts < self.last_ts:
                self.rb = (self.rb + 1) & 0xF
                logger.warning(f'clock rollback detected: {self.rb}')
                current_ts = ts_now()

            # 同一毫秒内处理序列号
            if current_ts == self.last_ts:
                self.seq = (self.seq + 1) & 0xFFFFFFF
                if self.seq == 0:  # 序列号溢出，强制推进时间
                    current_ts += 1
            else:
                self.seq = 0

            self.last_ts = current_ts

            snowflake_id = (
                (self.magic << (16 + 28 + 20 + 44 + 4))
                | self.rb << (16 + 28 + 20 + 44)
                | (current_ts << (16 + 28 + 20))
                | (self.node_id << (16 + 28))
                | self.seq << 16
                | time.thread_time_ns() & 0xFFFF
            )
            return snowflake_id

    def gen_uuid(self) -> uuid.UUID:
        return uuid.UUID(int=self.gen_id())
