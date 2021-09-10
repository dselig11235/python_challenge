from datetime import datetime, timedelta
from threading import RLock
from time import sleep

class Ratelimit:
    """Ratelimit decorator"""
    def __init__(self, limit, period):
        self.limit = limit
        self.period = period
        self.newPeriod()
        self.lock = RLock()
    def newPeriod(self):
        self.period_start=datetime.now()
        self.period_end=datetime.now() + timedelta(seconds=self.period)
        self.num_calls = 0
    def __call__(self, coro):
        async def ratelimited(*args, **kwargs):
            with self.lock:
                if self.period_end < datetime.now():
                    self.newPeriod()
                elif self.num_calls >= self.limit:
                    sleep((self.period_end - datetime.now()).total_seconds())
                    self.newPeriod()
                self.num_calls += 1
                return await fn(*args, **kwargs)
        return ratelimited
