#!/usr/bin/env python3

import os
import argparse

class TypeParser(argparse.ArgumentParser):
    """Argparser with custom arg types"""
    @staticmethod
    def list_of_ints(arg):
        return map(int, arg.split(','))
    
    @staticmethod
    def list_of_strings(arg):
        return arg.split(',')
    
    @staticmethod
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

    @staticmethod
    def list_of_trinarys(arg):
        if arg.lower() == 'all': return 'all'
        return [[int(num) for num in item.split(',')] for item in arg.split('/')]

class RegressionParser(TypeParser):        
    def print_help(self, file=None):
        import importlib
        import acq400_regression
        self.formatter_class.add_usage = self.null
        super().print_help(file)
        print()
        test_files = os.listdir( os.path.join( os.path.dirname(acq400_regression.__file__), 'tests') )
        excluded = ['__init__.py', 'generic.py']
        tests = [file.removesuffix('.py') for file in test_files if file.endswith('.py') if file not in excluded]
        for testname in tests:
            test = importlib.import_module(f"acq400_regression.tests.{testname}")
            parser = TypeParser(description=f"{testname.title()} test args:", add_help=False)
            test_class = getattr(test, testname.title())
            if not hasattr(test_class, 'get_args'):
                continue
            test_class.get_args(parser)
            parser.print_help()
            print()
            
    def null(*args, **kwargs):
        pass


def get_default_parser():
    parser = RegressionParser(description='acq400_regression default args', conflict_handler='resolve')
    
    #Global args
    parser.add_argument('--tests', '--test', type=parser.list_of_strings, help='list of tests post,prepost')
    parser.add_argument('--save',default=1, type=int, help='0: no save 1: save results + plot to file')
    parser.add_argument('--url', default=None, help='remote server to post results')
    parser.add_argument('--channels', default=[1], type=parser.list_of_channels, help=f"Channels to test 1,2,3,4 or all")
    parser.add_argument('--runs', default=1, type=int, help='How many tests to run of each type')
    parser.add_argument('--plot', default=1, type=int, help='Plot result 0: no plot, 1: plot, -1: plot on error')
    parser.add_argument('--divisor', default=20000, type=int, help="Divisor for clk freq") #chaneg to wavelen
    parser.add_argument('--cycles', default=1, type=int, help='number of cycles')
    parser.add_argument('--tolerance', default=0.035, type=float, help='wave comparison tolerance')
    parser.add_argument('--root', default='results', help=f"root dir to store results")
    parser.add_argument('--debug', default=False, action='store_true', help=f"Enabled debug")
    parser.add_argument('--master', default=None, help=f"override master uut")
    parser.add_argument('--master_role', default=None, help=f"master role")
    parser.add_argument('--spad', default='0,0,0', help=f"spad value")
    parser.add_argument('uutnames', nargs='+', help='list of uut hostnames')
    
    """
    #test specific arguments move elsewhere
    parser.add_argument('--triggers', default='all', type=parser.list_of_trinarys, help='Triggers to test 1,0,0/1,0,1/1,1,1 or all')
    parser.add_argument('--events', default='all', type=ArgTypes.list_of_trinarys, help='Events to test 1,0,0/1,0,1 or all')
    parser.add_argument('--pre', default=None, type=int, help='Pre samples')
    parser.add_argument('--post', default=None, type=int, help='Post samples')
    parser.add_argument('--translen', default=None, type=int, help=f"override rtm_translen")
    parser.add_argument('--runtime', default=None, type=int, help=f"override runtime")
    parser.add_argument('--timeout', default=None, type=int, help=f"override timeout")
    """
    return parser