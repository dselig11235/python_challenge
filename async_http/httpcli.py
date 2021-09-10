from .scheduler import HTTPScheduler
from cache import SimpleCache
import asyncio
import logging
log = logging.getLogger(__name__)

class HTTPCli:
    # Instantiating HTTPScheduler as a default argument here throws an error
    # since it relies on the asyncio loop which hasn't been started yet
    def __init__(self, scheduler=None, cache=None):
        if scheduler is None:
            self.scheduler = HTTPScheduler(16)
        else:
            self.scheduler = scheduler
        if cache is None:
            self.cache=SimpleCache()
        else:
            self.cache = cache
    async def get(self, url, priority=0):
        response = self.cache.lookup(url)
        if response is None:
            fut = await self.scheduler.submit(priority, url)
            response = await fut
            #response = await self.scheduler.submit(priority, url)
            self.cache.add(url, response)
        return response
    async def shutdown(self):
        await self.scheduler.shutdown()
