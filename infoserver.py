import traceback
from threading import Thread, Event
from queue import Queue, Empty
from cache import SimpleCache
from asyncio import Future
import asyncio
import logging
from async_http import HTTPCli
log = logging.getLogger(__name__)

from rdap import RDAPCli
from geo import GeoPlugin as GeoAPI

class InfoServer:
    def __init__(self, cache=None):
        #self.cache = SimpleCache() if cache is None else cache
        self.cache = cache
        self.thread = Thread(target=self.run)
        # Since we'll just have a single client and a single server, simple 
        # Qeues should work just fine
        # XXX counterintuitively, multiprocessing pipes might be faster
        # https://stackoverflow.com/questions/8463008/multiprocessing-pipe-vs-queue
        self.input = Queue()
        self.output = Queue()
        self.tasks = []
        self._shutdown_requested = False
    def start(self):
        self.thread.start()
    def run(self):
        log.debug('starting infoserver loop')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def cmdloop():
            if self.cache is None:
                self.cache = SimpleCache()
            else:
                self.cache = self.cache()
            self.rdap = RDAPCli()
            self.geo = GeoAPI()
            while not self._shutdown_requested:
                #log.debug('waiting for input')
                try:
                    cmd = self.input.get(timeout=.1)
                except Empty:
                    pass
                else:
                    log.debug(f'got command {cmd.__class__.__name__}')
                    await cmd.execute(self)
                    log.debug(f'finished command')
                if len(self.tasks) > 0:
                    done, pending = await asyncio.wait(self.tasks, timeout=.1)
                    for t in done:
                        try:
                            await t
                        except Exception as e:
                            log.error(f'Error in pending task: {e}')
                            log.debug(traceback.format_exc())
                    #log.debug(f'After waiting, harvested {len(done)} tasks and have {len(pending)} left')
                    self.tasks = pending
            #await asyncio.sleep(1)
            for t in asyncio.all_tasks():
                t.cancel()
                try:
                    await t
                except:
                    pass
        loop.run_until_complete(cmdloop())
        #loop.stop()
    def listIPs(self):
        return self.cache.list()
    async def add(self, ip, priority=20):
        log.debug(f'adding {ip} with priority {priority}')
        rdap = await self.rdap.lookup(ip, priority)
        geo = await self.geo.lookup(ip, priority)
        val = {'rdap': rdap, 'geo': geo}
        self.cache.add(ip, val)
        return val
    async def show(self, ip):
        val = self.cache.lookup(ip)
        if val is None:
            return await self.add(ip, 0)
        else:
            return val
    def backgroundTask(self, task):
        log.debug(f'backgrounding task of type {type(task)}')
        self.tasks.append(asyncio.create_task(task))
    async def sync(self, timeout=None):
        log.debug(f'syncing on {len(self.tasks)} tasks')
        #done, pending = await asyncio.wait(self.tasks)
        #self.tasks = pending
        #return (len(done), len(pending))
        rtn = await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks = []
        return rtn
    def rtn(self, val):
        log.debug(f'returning from rtn')
        self.output.put(val)
    async def shutdown(self):
        self._shutdown_requested = True
        for t in self.tasks:
            t.cancel()
        await self.rdap.shutdown()
        await self.geo.shutdown()
        await self.sync()

class Result:
    def __init__(self, cmd):
        self.cmd = cmd
        self.fut = Future()
        self.done = Event()
    def __await__(self):
        yield from self.fut
    def setResult(self, res):
        self.fut.set_result(res)
        self.done.set()
    def getResult(self):
        self.done.wait()
        return self.fut.result()

class Marshal:
    def __init__(self, backend):
        self.backend = backend
        self.backend.start()
    def submit(self, cmd):
        res = Result(cmd)
        self.backend.input.put(cmd)
        def setResult(res, outq):
            while True:
                try:
                    log.debug('waiting for output')
                    rtn = outq.get(timeout=1)
                    log.debug(f'got response in setResult')
                    res.setResult(rtn)
                    return rtn
                except Empty:
                    log.debug(f'waiting on output from command {res.cmd.__class__.__name__}')
        t = Thread(target=setResult, args=[res, self.backend.output])
        t.start()
        #asyncio.create_task(asyncio.to_thread(setResult))
        return res
