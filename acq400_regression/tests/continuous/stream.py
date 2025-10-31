from acq400_regression.tests.test_common import TestCommon
from acq400_regression.arg_parser import ArgTypes

"""
Stream

Test stream operation and data capture

Usage:
    acq400_regression test rtm acq1001_084 --siggen=SG0106 --runtime=30
"""

class Stream(TestCommon):

    all_triggers = ["1,1,1"]

    checks = ['spad']
    
    @classmethod
    def get_args(cls, parser):
        parser.add_argument('--runtime', default=30, type=int, help="stream runtime")
        parser.add_argument('--mask', default=[], type=ArgTypes.list_of_channels, help="Stream mask")

        return parser

    def start_test(self):
        return
        for params in self.get_run_parameters():
            self.start_run(**params)

    def start_run(self, post, trigger, event, translen, **kwargs):

        freq, voltage = self.calc_freq_and_voltage()
        period = self.get_translen_period(translen)
        self.siggen.config_waveform(freq, voltage)
        self.siggen.config_burst(burst=(event.source != 1), cycles=self.args.cycles, period=period)

        self.uuts.abort()

        self.uuts.setup(
            trigger=trigger,
            demux=self.args.demux,
            spad=self.args.spad,
        )

        for shot in self.get_run_shot():
            pass