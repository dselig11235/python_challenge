from async_http import HTTPCli
import json
import logging
log = logging.getLogger(__name__)
from async_http import Ratelimit, HTTPScheduler

class GeoPlugin:
    def __init__(self, cli=None, base='http://www.geoplugin.net/json.gp?ip='):
        self.base = base
        self.cli = HTTPCli(scheduler=HTTPScheduler(16, ratelimiter=Ratelimit(120, 60)))

    async def lookup(self, ip, priority):
        url = f'{self.base}{ip}'
        resp = await self.cli.get(url, priority)
        if resp is None:
            log.error(f'error while looking up Geolocation data for IP {ip}')
            return {}
        else:
            return json.loads(resp.data.decode("utf-8"))
    def shutdown(self):
        return self.cli.shutdown()

class IpApi:
    def __init__(self, cli=None, base='http://ip-api.com/json/'):
        self.base = base
        self.cli = HTTPCli() if cli is None else cli

    async def lookup(self, ip, priority):
        url = f'{self.base}{ip}'
        resp = await self.cli.get(url, priority)
        if resp is None:
            log.error(f'error while looking up Geolocation data for IP {ip}')
            return {}
        else:
            return json.loads(resp.data.decode("utf-8"))
