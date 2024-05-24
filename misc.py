#!/usr/bin/env python3

import logging
import argparse
from threading import Thread
from functools import wraps
import sys as _sys
import os

from acq400_hapi import pprint, PR #remove me

def all_uuts(func):
    """Runs passed function asynchronously for every uut"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        threads = []
        out = {}
        for uutname, uut in self.conns.items():
            thread = RThread(target=func, args=[self, uut, *args], kwargs=kwargs)
            threads.append(thread)
            thread.start()
        for thread in threads:
            out[uutname] = thread.join()
        return out
    return wrapper


def background_task(func):
    """Runs passed function in the background returns thread"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        thread = RThread(target=func, args=[self, *args], kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

def dio_uuts(func):
    """Runs passed function asynchronously for every uut with a dio"""
    #idk 
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        threads = []
        out = {}
        for uutname, uut  in self.conns.items():
            thread = RThread(target=func, args=[self, uut, *args], kwargs=kwargs)
            threads.append(thread)
            thread.start()
        for thread in threads:
            out[uutname] = thread.join()
        return out
    return wrapper
    
class DotDict(dict):
    __delattr__ = dict.__delitem__
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    
    def has(self, key):
        try: self[key]
        except:return False
        return True    
    
def tri(trinary, label=None, override=None, items=1):
    """helper function for trinary values"""
    enum = ['enabled', 'source', 'sense']
    trinary = trinary if type(trinary) == list else trinary.split(',')
    if label:
        if not override:
            return int(trinary[enum.index(label)])
        trinary[enum.index(label)] = override
    if items > 1: return trinary
    return ','.join(map(str, trinary))

def tri2(trinary, target=None, override=None, items=1):
    enum = ['enabled', 'source', 'sense']
    trinary = trinary if type(trinary) == list else trinary.split(',')
    if target:
        index = target if isinstance(target, int) else int(enum.index(target))
        

    return ','.join(map(str, trinary))
    
def custom_legend(plt):
    """Adds legend with click functions"""
    legend_map = {}
    legend = plt.legend(loc='upper right')
    legend.set_draggable(True)
    for lline, dline in zip(legend.get_lines(), plt.gca().get_lines()):
        lline.set_picker(5)
        legend_map[lline] = dline

    def on_pick_event(event):
        lline = event.artist
        if lline not in legend_map: return
        dline = legend_map[lline]
        visible = not dline.get_visible()
        dline.set_visible(visible)
        lline.set_alpha(1.0 if visible else 0.2)
        dline.figure.canvas.draw()

    plt.gcf().canvas.mpl_connect('pick_event', on_pick_event)  
    

class RThread(Thread):
    """Thread with return"""
    rtnval = None
    
    def run(self):
        self.rtnval = self._target(*self._args, **self._kwargs)
    
    def join(self):
        super().join()
        if type(self.rtnval) is Exception: raise self.rtnval
        return self.rtnval

def to_hex(num, pad=8):
    """Returns a zero padded hexadecimal string"""
    return f"{num:#0{pad + (3 if num < 0 else 2)}x}"

def ifnotset(value, default):
    """If value is set return value else default"""
    if value: return value
    return default

def print_dirs(rootdir):
    """Prints the contents of passed filepath"""
    
    print(f"[{rootdir}]")
    def printline(line, depth):
        pre=''
        pre += "│   " * depth
        if depth > 0: pre += "├──"
        print(f"{pre}{line}")
    
    rootdir = rootdir.rstrip('/')
    base_depth = len(rootdir.split('/'))
    for (root, dirs, files) in os.walk(rootdir, topdown=True):
        depth = len(root.split('/'))
        dirname = os.path.basename(root)
        if depth == base_depth:
            for idx, dirname in enumerate(root.split('/')):
                printline(f"📁 {dirname}/", idx)
        else:
            printline(f"📁 {dirname}/", depth)
            
        for filename in files:
            printline(filename, depth + 1)