
import os
import threading

class RThread(threading.Thread):
    """Thread with return"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rtnval = None
        self.exc = None
    
    def run(self):
        try: self.rtnval = self._target(*self._args, **self._kwargs)
        except Exception as e: self.exc = e
    
    def join(self, *args, **kwargs):
        super().join(*args, **kwargs)
        if self.exc: raise self.exc
        return self.rtnval

class Tri(str):
    """Helper class for Trinarys"""
    enum = ['enabled', 'source', 'sense']
    def __new__(cls, value):
        if isinstance(value, list):
            value = ",".join(map(str, value))
        return super().__new__(cls, value)
    
    def __getitem__(self, key):
        return int(self.split(',')[key])

    def __getattr__ (self, attr):
        if attr in self.enum:
            return int(self[self.enum.index(attr)])
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {attr!r}")
    
    def is_soft(self):
        return bool(int(list(self.split(','))[1]))
    
    def override(self, name, value):
        arr = list(self.split(','))
        arr[self.enum.index(name)] = str(value)
        return ','.join(arr)


class DotDict(dict):
    __delattr__ = dict.__delitem__
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

class DotDictAuto(DotDict):

    def __missing__(self, attr):
        self[attr] = DotDict()
        return self[attr]