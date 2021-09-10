from datetime import datetime, timedelta
from time import sleep
import asyncio
from asyncio import Lock
import logging
log = logging.getLogger(__name__)

class Ratelimit:
    """Ratelimit decorator"""
    def __init__(self, limit, period):
        self.limit = limit
        self.period = period
        self.newPeriod()
        self.lock = Lock()
    def newPeriod(self):
        log.debug('resetting ratelimit period')
        self.period_start=datetime.now()
        self.period_end=datetime.now() + timedelta(seconds=self.period)
        self.num_calls = 0
    def __call__(self, fn):
        async def ratelimited(*args, **kwargs):
            coro = fn(*args, **kwargs)
            async with self.lock:
                if self.period_end < datetime.now():
                    self.newPeriod()
                elif self.num_calls >= self.limit:
                    sleepfor = (self.period_end - datetime.now()).total_seconds()
                    log.debug(f'Ratelimit exceeded. Waiting {sleepfor} seconds')
                    await asyncio.sleep(sleepfor)
                    self.newPeriod()
                self.num_calls += 1
                return await coro
        return ratelimited
