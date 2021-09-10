from asyncio import PriorityQueue, Semaphore, Event
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
        self.is_started = False
        self.done = Event()
    def __lt__(self, other):
        return self.priority < other.priority
    def __eq__(self, other):
        return self.priority == other.priority
    def __bool__(self):
        return self.url is not None
    async def submit(self):
        self.request()
    async def start(self):
        log.debug(f'starting job for {self.url}')
        self.is_started = True
        self.response = await asyncio.to_thread(self.blocking_request)
        self.done.set()
        return self.response
    def blocking_request(self):
        #FIXME: We should handle exceptions where we actually use the results
        #instead of here. 
        try:
            return self.connection_pool.request('GET', self.url)
        except Exception as e:
            log.warning(f'Failed to retrieve url {self.url}')

class HTTPScheduler:
    def __init__(self, concurrency, ratelimiter = lambda x: x):
        self.ratelimiter = ratelimiter
        self.sem = Semaphore(concurrency)
        self.run_queue = PriorityQueue()
        self.connection_pool=urllib3.PoolManager(maxsize=10, retries = urllib3.Retry(2, redirect=5))
        self.start_task = asyncio.create_task(self.start())
        self.pending_requests = []
        self._shutdown_requested = False
    async def submit(self, priority, url):
        req = PriorityRequest(priority, url, self.connection_pool)
        await self.run_queue.put(req)
        async def onComplete(sem, job):
            try:
                log.debug(f'Waiting for job {job.url} to finish')
                await job.done.wait()
                log.debug(f'job {job.url} finished')
                return job.response
            except Exception as e:
                log.error(f'Error onComplete for PriorityRequest: {e}')
                return None
            finally:
                if job.is_started:
                    log.debug('Releasing HTTP scheduling semaphore')
                    sem.release()
        return asyncio.create_task(onComplete(self.sem, req))
    async def start(self):
        ratelimited = self.ratelimiter(self.getNext)
        while(True):
            job = await ratelimited()
            if job and not self._shutdown_requested:
                self.pending_requests.append(asyncio.create_task(job.start()))
            else:
                log.info('HTTPScheduler shutting down')
                return None
    async def getNext(self):
        log.debug('scheduler waiting on semaphore')
        await self.sem.acquire()
        log.debug('scheduler acquired semaphore')
        return await self.run_queue.get()
    async def shutdown(self):
        log.debug('Sending shutdown')
        req = PriorityRequest(-20, None, None)
        self._shutdown_requested=True
        await self.run_queue.put(req)
