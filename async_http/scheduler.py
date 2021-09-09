from asyncio import PriorityQueue, Semaphore, Future
import asyncio
import urllib3
from functools import total_ordering
import logging
log = logging.getLogger(__name__)

@total_ordering
class PriorityRequest:
    def __init__(self, priority, url, pool):
        self.url = url
        self.response = None
        self.connection_pool = pool
        self.priority = priority
        self.future = Future()
    def __lt__(self, other):
        return self.priority < other.priority
    def __eq__(self, other):
        return self.priority == other.priority
    def __bool__(self):
        return self.url is not None
    async def submit(self):
        self.request()
    async def start(self):
        try:
            self.future.set_result(await asyncio.to_thread(self.blocking_request))
        except Exception as e:
            self.future.set_exception(e)
    def blocking_request(self):
        return self.connection_pool.request('GET', self.url)

class HTTPScheduler:
    def __init__(self, concurrency):
        self.sem = Semaphore(concurrency)
        self.run_queue = PriorityQueue()
        self.connection_pool=urllib3.PoolManager(maxsize=10, retries = urllib3.Retry(2, redirect=5))
        asyncio.create_task(self.start())
    async def submit(self, priority, url):
        req = PriorityRequest(priority, url, self.connection_pool)
        await self.run_queue.put(req)
        def semReleaser(sem):
            def release(fut):
                log.debug('Releasing HTTP scheduling semaphore')
                sem.release()
            return release
        req.future.add_done_callback(semReleaser(self.sem))
        return req.future
    async def start(self):
        while(True):
            log.debug('scheduler waiting on semaphore')
            await self.sem.acquire()
            log.debug('scheduler acquired semaphore')
            job = await self.run_queue.get()
            if job:
                asyncio.create_task(job.start())
            else:
                log.info('HTTPScheduler shutting down')
                break
    async def shutdown(self):
        log.debug('Sending shutdown')
        req = PriorityRequest(-20, None, None)
        await self.run_queue.put(req)
