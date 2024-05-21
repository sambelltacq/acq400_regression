#!/usr/bin/env python3

"""Tests uuts streaming"""

from acq400_regression.BaseTest import BaseTest


class StreamTest(BaseTest):
    test_type = "stream"

    dir_fmt = "{type}_{runtime}s"
    
    @staticmethod
    def get_args(parser):
        """Test specific arguments"""
        parser.add_argument('--siggen',  help='signal generator hostname', required=True)
        parser.add_argument('--runtime', default=30, type=int, help=f"stream runtime")
        parser.add_argument('--triggers', default='all', type=parser.list_of_trinarys, help='Triggers to test 1,0,0/1,0,1/1,1,1 or all')
        return parser

    def run(self):
        self.save_state('runtime', self.args.runtime)
        self.wavelength = self.args.divisor #add into args
        
        freq, voltage = self.get_freq_and_voltage()
        self.siggen.config_params(freq, voltage)
        self.siggen.config_contiguous()
        
        self.uuts.setup(trg='1,0,1')

        self.run_iters()
        
        if self.args.save: self.th.save_test()
        self.th.stash_results()
        
        self.log.info(f"[{self.th.testname.title()}] Test Completed")
        
    def run_iters(self):
        
        for run in self.get_run():
            results = []
            self.uuts.abort()
            
            self.log.info(f"Streaming to host for {self.args.runtime}s")
            
            self.uuts.stream_to_host(runtime=self.args.runtime)
            
            dataset = self.th.import_dataset('HOST')
            results.append(self.check_spad(dataset))
            
            if not self.check_passed(results): break
        self.log.info(f"All runs complete {self.run}/{self.runs}") 
            
            
if __name__ == '__main__':
    from acq400_regression import Test_Handler
    
    args = Test_Handler.parser_args()
    th = Test_Handler(uutnames=args.uutnames, args=args)
    th.run_test('stream')