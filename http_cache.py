import requests
from datetime import timedelta, datetime
from logging import debug, info, warning, error, exception
from asyncio import PriorityQueue, Semaphore, Future
import asyncio
from threading import Condition, Event, Thread
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import urllib3
from functools import total_ordering

#for debugging
from time import sleep

# Base cache class
class Cache:
    '''Base cache class'''
    def __init__(self, ttl=timedelta(days=1)):
        self.ttl = ttl
    def lookup(self, key):
        raise Exception("lookup function not implemented in class self.__class__.__name__")
    def add(self, key, val):
        raise Exception("add function not implemented in class self.__class__.__name__")
    def remove(self, key):
        raise Exception("remove function not implemented in class self.__class__.__name__")

class NoCache(Cache):
    '''Dummy class providing no caching'''
    def lookup(self, key, val):
        return None
    def add(self, key, val):
        pass
    def remove(self, key, val):
        pass

class SimpleCache(Cache):
    '''Very simple cache using an in-memory Python dict. Should be fine for small sets'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}
    def lookup(self, key):
        '''Lookup a URL. Return None if it's not found or if the ttl is expired'''
        if not key in self.cache:
            return None
        elif self.cache[key]['expires'] < datetime.now():
            self.remove(key)
            return None
        else:
            return self.cache[key]['val']
    def add(self, key, val):
        self.cache[key] = {'val': val, 'expires': datetime.now()+self.ttl}
    def remove(self, key):
        del self.cache[key]

@total_ordering
class PriReq:
    def __init__(self, priority, url, pool):
        self.url = url
        self.response = None
        self.done = Event()
        self.connection_pool = pool
        self.priority = priority
        self.future = Future()
    def __lt__(self, other):
        return self.priority < other.priority
    def __eq__(self, other):
        return self.priority == other.priority
    async def submit(self):
        self.request()
    async def start(self):
        try:
            self.future.set_result(await asyncio.to_thread(self.blocking_request))
        except Exception as e:
            self.future.set_exception(e)
    def blocking_request(self):
        return self.connection_pool.request('GET', self.url)

class Sch:
    def __init__(self, concurrency):
        self.sem = Semaphore(concurrency)
        self.run_queue = PriorityQueue()
        self.connection_pool=urllib3.PoolManager(maxsize=10, retries = urllib3.Retry(2, redirect=5))
        asyncio.create_task(self.start())
    async def submit(self, priority, url):
        req = PriReq(priority, url, self.connection_pool)
        await self.run_queue.put(req)
        def semReleaser(sem):
            def release(fut):
                debug('Releasing HTTP scheduling semaphore')
                sem.release()
            return release
        req.future.add_done_callback(semReleaser(self.sem))
        return req.future
    async def start(self):
        while(True):
            debug('scheduler waiting on semaphore')
            await self.sem.acquire()
            debug('scheduler acquired semaphore')
            job = await self.run_queue.get()
            if job:
                asyncio.create_task(job.start())
            else:
                break
    def shutdown():
        self.run_queue.put(None)
