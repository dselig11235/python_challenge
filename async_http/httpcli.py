from .scheduler import HTTPScheduler
from .cache import SimpleCache
import asyncio

class HTTPCli:
    def __init__(self, scheduler=None, cache=SimpleCache()):
        if scheduler is None:
            self.scheduler = HTTPScheduler(16)
        else:
            self.scheduler = scheduler
        self.cache = cache
    async def get(self, url):
        response = self.cache.lookup(url)
        if response is None:
            fut = await self.scheduler.submit(0, url)
            response = await fut
            self.cache.add(url, response)
        return response
    def precache(self, urls):
        asyncio.create_task(self._precache(urls))
    async def _precache(self, urls):
        stale = [url for url in urls if self.cache.lookup(url) is None]
        futs = []
        for url in stale:
            futs.append(await self.scheduler.submit(20, url))
        return asyncio.gather(*futs)
