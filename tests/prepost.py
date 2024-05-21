#!/usr/bin/env python3

"""Tests prepost transient"""

from acq400_regression.tests.generic import generic
from acq400_regression.misc import tri

from acq400_hapi import PR, pprint, pv #remove me after testing


class Prepost(generic):
    test_type = "prepost"
    
    triggers = [
        [1,0,0],
        [1,0,1],
        [1,1,1],
    ]

    dir_fmt = "{type}_trg{trigger}_evt{event}"
    
    @staticmethod
    def get_args(parser):
        """Test specific arguments"""
        parser.add_argument('--siggen',  help='signal generator hostname', required=True)
        parser.add_argument('--post', default=50000, type=int, help='Post samples')
        parser.add_argument('--pre', default=50000, type=int, help='Pre samples')
        parser.add_argument('--triggers', default='all', type=parser.list_of_trinarys, help='Triggers to test 1,0,0/1,0,1/1,1,1 or all')
        parser.add_argument('--events', default='all', type=parser.list_of_trinarys, help='Events to test 1,0,0/1,0,1 or all')
        return parser
        
    def run(self):
        self.post = self.args.post
        self.save_state('post', self.post)
        
        self.pre = self.args.pre
        self.save_state('pre', self.pre)
        
        self.wavelength = self.args.divisor
        
        freq, voltage = self.get_freq_and_voltage()

        for trigger in self.get_trigger():
            for event in self.get_event():

                self.siggen.config_params(freq, voltage)
                self.siggen.config_trigger(trigger, self.args.cycles)

                self.run_iters(trigger, event)
                
                if self.args.save: self.th.save_test()
                self.th.stash_results()
                
        self.log.info(f"[{self.th.testname.title()}] Test Completed")
        
    #@generic.catch_error
    def run_iters(self, trigger, event):
        for run in self.get_run():
            self.log.info(f"[{self.test_type}] Trigger {trigger} Event {event}")
            
            results = []

            self.uuts.abort()

            self.uuts.transient(pre=self.pre, post=self.post, trg=trigger, evt=event)

            self.uuts.arm()
            self.log.info('Arming')

            self.uuts.wait_armed(timeout=45)
            self.log.info('Ready')

            if tri(trigger, 'source') != 1: self.siggen.trigger(delay=1)

            self.uuts.wait_pre_complete(2 * self.pre)

            if tri(event, 'source') != 1: self.siggen.trigger()

            self.uuts.wait_completed(timeout=60)
            self.log.info('Completed')

            dataset = self.th.offload_dataset()
            
            ideal_wave, tolerance, dtype = self.get_ideal_wave(dataset, self.is_soft(trigger), self.is_rising(event))
            
            results.append(self.check_wave_synchronous(dataset, ideal_wave, tolerance))

            if not self.check_passed(results): break
        
        self.log.info(f"All runs complete {run}/{self.args.runs}")