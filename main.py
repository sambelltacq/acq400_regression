#!/usr/bin/env python3

"""Example acq400_regression init script

    ./acq400_regression/main.py --test=stream --siggen=SG1923 acq2106_396
"""

from acq400_regression import Test_Handler
            
def run_main(args):
    #dev testing
    #args.siggen = 'SG0761' # acq2106_130
    #args.siggen = 'SG2862' # acq2106_130
    #args.siggen = 'SG0138' # acq1001_652
    #args.siggen = 'SG0106' #acq2106_133
    #args.siggen = 'SG0153' # acq1001_578
    #args.triggers = [[1,0,1]]
    #args.root = 'results_dev' #dev override
    th = Test_Handler(uutnames=args.uutnames, args=args)
    th.run_tests(args.tests)

if __name__ == '__main__':
    run_main(Test_Handler.parser.parse_known_args()[0])
