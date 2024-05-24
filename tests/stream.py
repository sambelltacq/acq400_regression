#!/usr/bin/env python3

"""Tests uuts streaming"""

from acq400_regression.BaseTest import BaseTest
from acq400_regression.misc import tri

class StreamTest(BaseTest):
    test_type = "stream"

    dir_fmt = "{type}_{runtime}s"
    
    @staticmethod
    def get_args(parser):
        """Test specific arguments"""
        parser.add_argument('--siggen',  help='signal generator hostname', required=True)
        parser.add_argument('--runtime', default=5, type=int, help=f"stream runtime")
        parser.add_argument('--period', default=0.2, type=float, help=f"override burst period")
        parser.add_argument('--triggers', default='all', type=parser.list_of_trinarys, help='Triggers to test 1,0,0/1,0,1/1,1,1 or all')
        return parser

    def run(self):
        self.save_state('runtime', self.args.runtime)
        self.wavelength = self.args.wavelength #add into args
        
        clk = [uut.clk for uut in self.uuts][0] #TODO make nicer
        tlen = self.wavelength * self.args.cycles
        self.period = round(tlen / clk * 3, 2)
        print(f"period {self.period}")
        
        freq, voltage = self.get_freq_and_voltage()
        
        
        for trigger in self.get_trigger():
            trigger = '1,0,1' #decide test triggers
            
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
            
            #TODO: check waveform here
            
            if not self.check_passed(results): break
        self.log.info(f"All runs complete {self.run}/{self.runs}") 
            
            
if __name__ == '__main__':
    from acq400_regression import Test_Handler
    
    args = Test_Handler.parser_args()
    th = Test_Handler(uutnames=args.uutnames, args=args)
    th.run_test('stream')