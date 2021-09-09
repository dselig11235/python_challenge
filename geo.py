from async_http import HTTPCli
import json

class GeoPlugin:
    def __init__(self, cli=None, base='http://www.geoplugin.net/json.gp?ip='):
        self.base = base
        self.cli = HTTPCli() if cli is None else cli

    async def lookup(self, ip, priority):
        url = f'{self.base}{ip}'
        resp = await self.cli.get(url, priority)
        return json.loads(resp.data.decode("utf-8"))
