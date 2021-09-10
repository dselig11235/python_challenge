from async_http import HTTPCli
import json
import logging
log = logging.getLogger(__name__)

class RDAPCli:
    def __init__(self, cli=None, bootstrap='https://rdap-bootstrap.arin.net/bootstrap'):
        self.bootstrap = bootstrap
        self.cli = HTTPCli() if cli is None else cli

    async def lookup(self, ip, priority):
        url = f'{self.bootstrap}/ip/{ip}'
        resp = await self.cli.get(url, priority)
        if resp is None:
            log.error(f'error while looking up RDAP data for IP {ip}')
            return {}
        else:
            return json.loads(resp.data.decode("utf-8"))
    def shutdown(self):
        return self.cli.shutdown()
