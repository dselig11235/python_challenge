from datetime import timedelta, datetime
from abc import ABC, abstractmethod

# Base cache class
class Cache(ABC):
    '''Base cache class'''
    def __init__(self, ttl=timedelta(days=1)):
        self.ttl = ttl
    @abstractmethod
    def lookup(self, key):
        raise NotImplemented("lookup function not implemented in class self.__class__.__name__")
    @abstractmethod
    def add(self, key, val):
        raise NotImplemented("add function not implemented in class self.__class__.__name__")
    @abstractmethod
    def remove(self, key):
        raise NotImplemented("remove function not implemented in class self.__class__.__name__")
    @abstractmethod
    def list(self):
        raise NotImplemented("list function not implemented in class self.__class__.__name__")

class NoCache(Cache):
    '''Dummy class providing no caching'''
    def lookup(self, key, val):
        return None
    def add(self, key, val):
        pass
    def remove(self, key):
        pass
    def list(self):
        return []

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
    def list(self):
        return self.cache.keys()
