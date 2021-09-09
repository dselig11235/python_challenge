from abc import ABC, abstractmethod
import re
import logging
log = logging.getLogger(__name__)

class IPInfoCmd(ABC):
    '''Abstract class for commands to send to the thread running the geo and
    rdap lookup services'''
    @abstractmethod
    def execute(self, target):
        raise NotImplementedError()

class ListIPs(IPInfoCmd):
    '''List IPs matching the provided regex'''
    def __init__(self, regex = None):
        self.regex=regex
    async def execute(self, target):
        if self.regex:
            ip_re = re.compile(self.regex)
            test = lambda x: ip_re.match(x)
        else:
            test = lambda x: True
        target.rtn([ip for ip in target.listIPs() if test(ip)])

class Precache(IPInfoCmd):
    '''Start caching a list of IPs in the background'''
    def __init__(self, ips):
        self.ips=ips
    async def execute(self, target):
        for ip in self.ips:
            target.backgroundTask(target.add(ip))
        # Have to return something
        target.rtn(None)

class Sync(IPInfoCmd):
    '''Wait until all background tasks have completed'''
    async def execute(self, target):
        target.rtn(await target.sync(1))

class Show(IPInfoCmd):
    def __init__(self, ip):
        self.ip = ip
    async def execute(self, target):
        info = await target.show(self.ip)
        target.rtn(info)

class Shutdown(IPInfoCmd):
    async def execute(self, target):
        await target.shutdown()
        target.rtn(None)
