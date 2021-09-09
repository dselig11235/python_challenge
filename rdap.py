from async_http import HTTPCli
import json

class RDAPCli:
    def __init__(self, cli=None, bootstrap='https://rdap-bootstrap.arin.net/bootstrap'):
        self.bootstrap = bootstrap
        self.cli = HTTPCli() if cli is None else cli

    async def lookup(self, ip, priority):
        url = f'{self.bootstrap}/ip/{ip}'
        resp = await self.cli.get(url, priority)
        return json.loads(resp.data.decode("utf-8"))
