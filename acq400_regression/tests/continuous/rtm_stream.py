from acq400_regression.tests.test_common import TestCommon
from acq400_regression.arg_parser import ArgTypes

"""
RTM Stream

Test stream operation and data capture

Usage:
    acq400_regression test rtm_stream acq1001_084 --siggen=SG0106 --runtime=30
"""

#TODO fix underscores in test names

class RTM_Stream(TestCommon):

    all_triggers = ["1,1,1"]

    checks = ['spad']

    all_rgms= ["3,0,1"]

    run_params = ['runtime', 'post', 'trigger', 'rgm', 'translen']
    
    @classmethod
    def get_args(cls, parser):
        parser.add_argument('--runtime', default=30, type=int, help="stream runtime")
        parser.add_argument('--mask', default=[], type=ArgTypes.list_of_channels, help="Stream mask")
        parser.add_argument('--rgm', '--rgms', default='all', type=ArgTypes.list_of_trinarys(cls.all_rgms), help='Triggers to test 3,0,1 or all')
        parser.add_argument('--translen', default=5000, type=int, help="rtm_translen value")
        return parser

    def start_test(self):
        print("Not ready")
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