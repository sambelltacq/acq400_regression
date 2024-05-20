#!/usr/bin/env python3

import logging
import argparse
from threading import Thread
from functools import wraps
import sys as _sys

from acq400_hapi import pprint, PR #remove me

def all_uuts(func):
    """Runs passed function asynchronously for every uut"""
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


def backstage(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        thread = RThread(target=func, args=[self, *args], kwargs=kwargs)
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


class ArgTypes:#rework me
    def list_of_ints(arg):
        return map(int, arg.split(','))

    def list_of_strings(arg):
        return arg.split(',')
    
    def list_of_channels(arg):
        #1,3-5 = 1,3,4,5
        if arg.lower() == 'all': return 'all'
        channels = []
        for chan in arg.split(','):
            if '-' in chan:
                chan = list(map(int, chan.split('-')))
                channels.extend(list(range(chan[0], chan[1] + 1)))
                continue
            channels.append(int(chan))
        return channels

    def list_of_trinarys(arg):
        if arg.lower() == 'all': return 'all'
        return [[int(num) for num in item.split(',')] for item in arg.split('/')]
    
    class Trinary(list):
        enum = ['enabled', 'source', 'sense']    
        def __init__(self, value):
            value = value if type(value) == list else list(map(int, value.split(',')))
            super().__init__(value)
            
        def __str__(self):
            return ','.join(map(str, self))

class DotDict2(dict):
    __delattr__ = dict.__delitem__

    def __getattr__(self, attr):
        if attr not in self: self[attr] = DotDict()
        return self[attr]
    
    def __setattr__(self, attr, value):
        self[attr] = value

    def __missing__(self, idx):
        self[idx] = DotDict()
        return self[idx]
    
class DotDict3(dict): #simpler
    __delattr__ = dict.__delitem__

    def __getattr__(self, attr):
        return self[attr]
    
    def __setattr__(self, attr, value):
        print(f"[DotDict] __setattr__ {attr} = {value}")
        self[attr] = value
        
    def __missing__(self, idx):
        print(f"[DotDict] __missing__ {idx}")
        return self[idx]
    
    def has(self, key):
        try: self[key]
        except:return False
        return True
    
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
    
    


def hstl(stl):
    """helper functions for stl values"""
    #ie add new lines if list and append eof 
    return stl

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
    
    
def get_default_parser():
    parser = CustomArgumentParser(description='acq400_regression default argparser', conflict_handler='resolve')
    
    #Global args
    parser.add_argument('--tests', '--test', type=ArgTypes.list_of_strings, required=True, help='list of tests post,prepost')
    parser.add_argument('--save', type=int, default=1, help='0: no save 1: save results + plot to file')
    parser.add_argument('--url', default=None, help='remote server to post results')
    parser.add_argument('--channels', type=ArgTypes.list_of_channels, default=[1], help=f"Channels to test 1,2,3,4 or all")
    parser.add_argument('--runs', default=1, type=int, help='How many tests to run of each type')
    parser.add_argument('--plot', default=1, type=int, help='Plot result 0: no plot, 1: plot, -1: plot on error')
    parser.add_argument('--divisor', default=20000, type=int, help="Divisor for clk freq") #chaneg to wavelen
    parser.add_argument('--cycles', default=1, type=int, help='number of cycles')
    parser.add_argument('--tolerance', default=0.035, type=float, help='wave comparison tolerance')
    parser.add_argument('--root', default='results', help=f"root dir to store results")
    parser.add_argument('--debug', default=False, action='store_true', help=f"Enabled debug")
    parser.add_argument('--master', default=None, help=f"override master uut")
    parser.add_argument('--master_role', default=None, help=f"master role")
    parser.add_argument('--spad', default=None, help=f"spad value")
    #parser.add_argument('--spad', default=None, type=ArgTypes.Trinary, help=f"spad value") #TODO
    parser.add_argument('uutnames', nargs='+', help='list of uut hostnames')
    
    """
    #test specific arguments move elsewhere
    parser.add_argument('--triggers', default='all', type=ArgTypes.list_of_trinarys, help='Triggers to test 1,0,0/1,0,1/1,1,1 or all')
    parser.add_argument('--events', default='all', type=ArgTypes.list_of_trinarys, help='Events to test 1,0,0/1,0,1 or all')
    parser.add_argument('--pre', default=None, type=int, help='Pre samples')
    parser.add_argument('--post', default=None, type=int, help='Post samples')
    parser.add_argument('--translen', default=None, type=int, help=f"override rtm_translen")
    parser.add_argument('--runtime', default=None, type=int, help=f"override runtime")
    parser.add_argument('--timeout', default=None, type=int, help=f"override timeout")
    """
    return parser


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


import os
import importlib
import acq400_regression

class CustomArgumentParser(argparse.ArgumentParser):        
    def print_help(self, file=None):
        self.formatter_class.add_usage = self.null
        super().print_help(file)
        
        test_files = os.listdir( os.path.join( os.path.dirname(acq400_regression.__file__), 'tests') )
        excluded = ['__init__.py', 'generic.py']
        tests = [file.removesuffix('.py') for file in test_files if file.endswith('.py') if file not in excluded]
        PR.Yellow(tests)
        for testname in tests:
            test = importlib.import_module(f"acq400_regression.tests.{testname}")
            parser = argparse.ArgumentParser(description=test.__doc__, add_help=False)
            test_class = getattr(test, testname.title())
            if not hasattr(test_class, 'get_args'):
                print(f"{testname} invalid argparser")
                continue
            test_class.get_args(parser)
            parser.print_help()
            print()