from cmd import Cmd
from parser import IPExtractor
from rdap import RDAPCli
from infoserver import Marshal, InfoServer
from commands import *
import asyncio
import logging
import shutil
import json
from pathlib import Path
import traceback

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

# getch gets one character at a time
try:
    #Microsoft library has getch
    from msvcrt import getch
except ImportError:
    #If we're not on MS, set up the low-level terminal stuff for raw input
    import tty, sys, termios
    def getch():
        fd = sys.stdin.fileno()
        saved = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, saved)

def page(lines):
    '''Simple pager takes an array of lines to show'''
    nlines = shutil.get_terminal_size()[1] - 1
    def getContinue():
        while True:
            c = getch()
            if c == 'q' or c == ' ':
                return c
    for idx in range(0, len(lines), nlines):
        for ln in lines[idx:idx+nlines]:
            print(ln)
        msg = "Press [SPACE] for more or 'q' to quit"
        print(msg, end='\r')
        c = getContinue()
        print(' '*len(msg), end='\r')
        if c == 'q':
            break

def exceptionHandled(fn):
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            log.error(f'Exception in {fn.__name__}: {e}')
            log.debug(traceback.format_exc())
    # Need docstrings for help pages in cli
    wrapped.__doc__ = fn.__doc__
    return wrapped

class IPLookup(Cmd):
    prompt = '> '
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.do_EOF = self.do_exit
    def preloop(self):
        '''Set up backend thread and marshaller'''
        self.marshaller = Marshal(InfoServer())
    def emptyline(self):
        pass
    @exceptionHandled
    def do_parse(self, filename):
        '''Parse a file and extract all IPv4 addresses'''
        with open(filename) as f:
            ips = IPExtractor(f.read())
        self.marshaller.submit(Precache(ips))
    def complete_parse(self, text, ln, beg, end):
        path = ln.split(maxsplit=1)
        if len(path) == 1:
            path = ''
        else:
            path = path[1]
        p = Path(path)
        if p.is_dir():
            par=p
            name=''
        else:
            par=p.parent
            name=p.name
        return [str(p.name) for p in par.glob(name+'*')]
    @exceptionHandled
    def do_list(self, ip_re):
        '''List IPs that are either pending or already cached. IPs present in
        the cache and available for immediate retrieval are preceded by a  "*"'''
        ips = self.marshaller.submit(ListIPs(ip_re)).getResult()
        page(ips)
    @exceptionHandled
    def do_show(self, ip):
        '''Print the rdap and geolocation information for an IP'''
        #TODO: implement some subset of jsonpath to allow filtering the output
        info = self.marshaller.submit(Show(ip)).getResult()
        page(json.dumps(info, indent=4).split('\n'))
    def complete_show(self, text, ln, beg, end):
        ips = self.marshaller.submit(ListIPs('')).getResult()
        return [ip for ip in ips if ip.startswith(text)]
    @exceptionHandled
    def do_sync(self, _):
        '''Wait for all pending caching'''
        stop = False
        while not stop:
            #numDone, numPending = self.marshaller.submit(Sync()).getResult()
            #print(f'{numDone} tasks completed, {numPending} still pending')
            self.marshaller.submit(Sync()).done.wait()
    @exceptionHandled
    def do_exit(self, _):
        '''Try to abort any pending requests and shut everything down'''
        self.marshaller.submit(Shutdown()).done.wait()
        return True

if __name__ == '__main__':
    IPLookup().cmdloop()
