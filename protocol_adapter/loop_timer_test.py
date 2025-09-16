#!/usr/bin/python3
# Copyright 2024 Standard Robots Co. All rights reserved.
import unittest
import time

from protocol_adapter.loop_timer import LoopTimer

num = 0
arg1 = None
arg2 = None


def func(a, b):
    global num
    global arg1
    global arg2
    num += 1
    arg1 = a
    arg2 = b


class LoopTimerTest(unittest.TestCase):
    def test_base(self):
        ARG1 = 'abc'
        ARG2 = 7777
        increment_timer = LoopTimer(0.001, func, 0.01, name='test_base', args=[ARG1, ARG2])
        increment_timer.start()
        time.sleep(0.1)
        self.assertGreater(num, 0)
        self.assertEqual(arg1, ARG1)
        self.assertEqual(arg2, ARG2)


if __name__ == '__main__':
    unittest.main()
