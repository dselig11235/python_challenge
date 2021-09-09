from datetime import timedelta, datetime
from logging import debug, info, warning, error, exception

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


