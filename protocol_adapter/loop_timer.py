import threading


class Timer(threading.Thread):
    """创建一个线程，等待一定时间后执行一次回调函数"""

    def __init__(self, interval, cb, live_time=-1, name=None, args=list(), kwargs=dict()):
        threading.Thread.__init__(self, name=name)
        self.interval = interval
        self.callback = cb
        self.live_time = live_time
        self.args = args
        self.kwargs = kwargs
        self.finished = threading.Event()

    def cancel(self):
        self.finished.set()

    def run(self):
        self.finished.wait(self.interval)
        if not self.finished.is_set():
            self.callback(*self.args, **self.kwargs)
        self.finished.set()

    def is_finished(self):
        return self.finished.is_set()


class LoopTimer(Timer):
    def __init__(self, interval, cb, live_time=-1, name=None, args=list(), kwargs=dict()):
        Timer.__init__(self, interval, cb, live_time, name, args, kwargs)

    def run(self):
        trigger_cnt = 0
        while True:
            if self.live_time > 0 and (trigger_cnt * self.interval >= self.live_time):
                self.cancel()
            if not self.finished.is_set():
                self.finished.wait(self.interval)
                # 等待时间到后，如果已经取消，则不要触发回调
                if self.finished.is_set():
                    break
                trigger_cnt += 1
                self.callback(*self.args, **self.kwargs)
            else:
                break
