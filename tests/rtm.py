#!/usr/bin/env python3

"""Tests uuts rtm transient shot"""

from acq400_regression.tests.generic import generic
from acq400_regression.misc import tri, custom_legend, to_hex, ifnotset

from acq400_hapi import PR, pprint, pv #remove me after testing


from acq400_regression.analysis import Waveform

from matplotlib import pyplot as plt

import time


import numpy as np

class Rtm(generic):
    test_type = "rtm"

    post = 100000
    translen = 5000

    rgm = [3,0,1]
    
    dir_fmt = "{type}_trg{trigger}_evt{event}"
    
    def get_args2(self, parser):
        parser.add_argument('--abcdef', default=None, type=int, help=f"override rtm_translen")
        return parser

    def run(self):

        self.post = ifnotset(self.args.post, self.post)
        self.save_state('post', self.post)
        
        self.translen = ifnotset(self.args.translen, self.translen)
        self.save_state('translen', self.translen)

        self.wavelength = self.args.divisor
                
        freq, voltage = self.get_freq_and_voltage()

        for trigger in self.get_trigger():
            for event in self.get_event():

                self.siggen.config_params(freq, voltage)
                self.siggen.config_trigger(trigger, self.args.cycles)
                self.siggen.config_rgm(self.rgm, self.args.cycles)
                
                self.run_iters(trigger, event)
            
                if self.args.save: self.th.save_test()
                self.th.stash_results()
                
        self.log.info(f"[{self.th.testname.title()}] Test Completed")
        
    #@generic.catch_error
    def run_iters(self, trigger, event):
        for run in self.get_run():
            results = []

            self.uuts.abort()
            
            self.uuts.transient(post=self.post, trg=trigger, evt=event, rgm=self.rgm, translen=self.translen)

            self.uuts.arm()
            self.log.info('Arming')

            self.uuts.wait_armed()
            self.log.info('Ready')
            
            self.uuts.wait_completed()
            self.log.info('Completed')
            
            dataset = self.th.offload_dataset()
            
            results.append(self.check_es(dataset))
            
            ideal_wave, tolerance, dtype = self.get_ideal_wave(dataset)       
            results.append(self.check_wave_synchronous(dataset, ideal_wave, tolerance))
            
            if not self.check_passed(results): break
            
        self.log.info(f"All runs complete {self.run}/{self.runs}")
