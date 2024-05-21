#!/usr/bin/env python3

"""Tests uuts post transient shot"""

from acq400_regression.tests.generic import generic
from acq400_regression.misc import tri

from acq400_hapi import PR, pprint #remove me after testing


class Post(generic):
    test_type = "post"

    post = 100000

    dir_fmt = "{type}_trg{trigger}"
    
    @staticmethod
    def get_args(parser):
        """Test specific arguments"""
        parser.add_argument('--siggen',  help='signal generator hostname', required=True)
        parser.add_argument('--post', default=100000, type=int, help='Post samples')
        parser.add_argument('--triggers', default='all', type=parser.list_of_trinarys, help='Triggers to test 1,0,0/1,0,1/1,1,1 or all')
        return parser

    def run(self):
        self.post = self.args.post
        self.save_state('post', self.post)
        
        self.wavelength = self.args.divisor
        freq, voltage = self.get_freq_and_voltage()

        for trigger in self.get_trigger():

            self.siggen.config_params(freq, voltage)
            self.siggen.config_trigger(trigger, self.args.cycles)
            
            self.run_iters(trigger)
            
            if self.args.save: self.th.save_test()
            self.th.stash_results()
        
        self.log.info(f"[{self.th.testname.title()}] Test Completed")
        
        
    #@generic.catch_error
    def run_iters(self, trigger):
        self.uuts.setup(post=self.post, trg=trigger)
        
        for run in self.get_run():
            self.log.info(f"[{self.test_type}] Trigger {trigger}")
            results = []
                            
            self.uuts.abort()
            self.uuts.arm()
            self.log.info('Arming')

            self.uuts.wait_armed()
            self.log.info('Ready')

            if tri(trigger, 'source') != 1: self.siggen.trigger(delay=1)

            self.uuts.wait_completed()
            self.log.info('Completed')

            dataset = self.th.import_dataset()
            
            results.append(self.check_spad(dataset))
            
            ideal_wave, tolerance, dtype = self.get_ideal_wave(dataset, self.is_soft(trigger), self.is_rising(trigger))
            results.append(self.check_wave(dataset, ideal_wave, tolerance))
            
            if not self.check_passed(results): break
            
        self.log.info(f"All runs complete {run}/{self.args.runs}")
        
if __name__ == '__main__':
    from acq400_regression import TestHandler
    
    args = TestHandler.parser_args()
    th = TestHandler(uutnames=args.uutnames, args=args)
    th.run_test('post')