#!/usr/bin/env python3

"""Example acq400_regression init script

    ./acq400_regression/main.py --test=stream --siggen=SG1923 acq2106_396
"""

from acq400_regression import TestHandler
            
def run_main(args):
    args.root = 'results_dev' #dev override
    
    th = TestHandler(uutnames=args.uutnames, args=args)
    th.run_tests(args.tests)

if __name__ == '__main__':
    run_main(TestHandler.parser_args())
