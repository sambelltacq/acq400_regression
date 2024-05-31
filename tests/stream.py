#!/usr/bin/env python3

"""Tests uuts streaming"""

from acq400_regression.BaseTest import BaseTest
from acq400_regression.misc import tri, ifnotset

from acq400_hapi import PR
from matplotlib import pyplot as plt

class StreamTest(BaseTest):
    test_type = "stream"

    dir_fmt = "{type}_{runtime}s"
    
    @staticmethod
    def get_args(parser):
        """Test specific arguments"""
        parser.add_argument('--siggen',  help='signal generator hostname', required=True)
        parser.add_argument('--runtime', default=5, type=int, help=f"stream runtime")
        parser.add_argument('--period', default=None, type=float, help=f"override burst period")
        parser.add_argument('--triggers', default='all', type=parser.list_of_trinarys, help='Triggers to test 1,0,0/1,0,1/1,1,1 or all')
        return parser

    def run(self):
        self.save_state('runtime', self.args.runtime)
        self.wavelength = self.args.wavelength #add into args
        
        self.period = ifnotset(self.args.period, self.get_burst_period(10))
        """
        burst period can be set automatically ro via arg
        
        translen must be calculated from period * CLk
        
        20,000 wavelength * 10 factor = 200,000
        
        
        0.2 * CLK
        
        """
        
        self.save_state('period', self.period)
        PR.Red(f"PERIOD is {self.period}")
        
        freq, voltage = self.get_freq_and_voltage()
        
        PR.Yellow(f"voltage is {voltage} freq is {freq}")
        
        for trigger in self.get_trigger():
            #trigger = '1,0,1' #decide test triggers
            
            self.siggen.config_params(freq, voltage)
            
            
            self.uuts.setup(trg=trigger)

            self.run_iters(trigger)
            
            if self.args.save: self.th.save_test()
            self.th.stash_results()
        
        self.log.info(f"[{self.th.testname.title()}] Test Completed")
        
    def run_iters(self, trigger):
        
        for run in self.get_run():
            results = []
            
            self.uuts.abort()
            
            self.log.info(f"Streaming to host for {self.args.runtime}s")
            
            
            self.siggen.enable_free_running_burst(self.args.cycles, self.period)
            self.uuts.init_stream_to_host(runtime=self.args.runtime)
        
            self.uuts.wait_armed()
            self.log.info('Ready')
            
            if tri(trigger, 'source') != 1: self.siggen.start_free_running_burst()
            
            self.uuts.wait_completed()
            self.log.info('Ready')
            
            dataset = self.th.import_dataset('HOST')
            results.append(self.check_spad(dataset))
            
            
            """clk = [uut.clk for uut in self.uuts][0]
            self.translen = int(self.period * clk)
            self.pre = 0
            self.post = dataset[self.uuts[0].hostname].datalen
            PR.Yellow(self.translen)
            ideal_wave, tolerance, dtype = self.get_ideal_wave(dataset)
            results.append(self.check_wave(dataset, ideal_wave, tolerance))"""
            
            if not self.check_passed(results): break
            #self.check_passed(results)
        self.log.info(f"All runs complete {self.run}/{self.runs}") 
            
            
if __name__ == '__main__':
    from acq400_regression import Test_Handler
    
    args = Test_Handler.parser_args()
    th = Test_Handler(uutnames=args.uutnames, args=args)
    th.run_test('stream')