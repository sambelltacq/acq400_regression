#!/usr/bin/env python3
"""
Command-line interface for ACQ400 Regression Testing Suite.



acq400_regression test post acq1001_084


"""

import sys

from acq400_regression.logging_config import setup_logging
from acq400_regression.controller import Controller
from acq400_regression.arg_parser import get_parser


def run_tests(args):
    """Run regression tests."""
    
    controller = Controller(args)
    for test in args[0].tests:
        controller.run_test(test)


    print("Done")



def main():
    parser = get_parser()
    args = parser.parse_known_args()
    #args[0].verbose = True # force verbose for dev
    setup_logging(getattr(args[0], 'verbose', False))

    if args[0].command == 'test':
        return run_tests(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
