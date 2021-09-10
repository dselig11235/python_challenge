from parser import IPExtractor
from rdap import RDAPCli
from geo import GeoPlugin
import asyncio
from asyncio import CancelledError
import logging
import shutil
from pathlib import Path
import traceback
from sqlite_cache import SQLiteCache

formatter = logging.Formatter('%(asctime)s %(levelname)s: [%(threadName)s][%(module)s]%(message)s', "%Y-%m-%d %H:%M:%S")
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.ERROR)
stream_handler.setFormatter(formatter)

file_handler = logging.FileHandler('cli.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(stream_handler)
log.addHandler(file_handler)

async def lookup(rdap, geo, cache, ip):
    rtn = {'rdap': {}, 'geo':{}}
    try:
        rtn['rdap'] = await rdap.lookup(ip, 0)
        rtn['geo'] = await geo.lookup(ip, 0)
        cache.add(ip, rtn)
        return rtn
    except CancelledError:
        return rtn
    except Exception as e:
        log.error(e)
        raise

async def addToCache(cache, ips):
    rdap = RDAPCli()
    geo = GeoPlugin()
    pending = [asyncio.create_task(lookup(rdap, geo, cache, ip)) for ip in ips]
    while(len(pending) > 0):
        done, pending = await asyncio.wait(pending, timeout=3)
        for t in done:
            try:
                await t
            except Exception as e:
                log.exception(e)
        print(f'{len(done)} tasks finished, {len(pending)} to go', end='\r')
    return True

async def parseAndCache(filename, cache):
    with open(filename) as f:
        ips = IPExtractor(f.read())
    return await addToCache(cache, ips)

async def main(command, args, cachefile='.cache.sqlite'):
    cache = SQLiteCache(cachefile)
    command_lu = {
            'parse': parseAndCache(args[0], cache)
            }
    return await command_lu[command]

if __name__ == '__main__':
    import sys
    asyncio.run(main('parse', [sys.argv[1]]))
