from acq400_regression.tests.test_common import TestCommon
from acq400_regression.arg_parser import ArgTypes

"""
Prepost

Test prepost transient operation and data capture

Usage:
    acq400_regression test rtm acq1001_084 --siggen=SG0106 --post=100000 --trigger=1,1,1 --event=1,0,1 --translen=5000
"""

class Rtm(TestCommon):

    all_triggers = ["1,1,1"]

    all_rgms= ["3,0,1"]

    run_params = ['post', 'trigger', 'rgm', 'translen']

    checks = ['spad', 'synchronous']
    
    @classmethod
    def get_args(cls, parser):
        parser.add_argument('--siggen', help='signal generator hostname', required=True)
        parser.add_argument('--post', default=100000, type=ArgTypes.list_of_ints, help='Post samples')
        parser.add_argument('--trigger', '--triggers', default='all', type=ArgTypes.list_of_trinarys(cls.all_triggers), help='Triggers to test 1,1,1 or all')
        parser.add_argument('--rgm', '--rgms', default='all', type=ArgTypes.list_of_trinarys(cls.all_rgms), help='Triggers to test 3,0,1 or all')
        parser.add_argument('--translen', default=5000, type=ArgTypes.list_of_ints, help="rtm_translen value")
        return parser

    def start_test(self):      
        for params in self.get_run_parameters():
            self.start_run(**params)

    def start_run(self, post, trigger, translen, rgm, **kwargs):

        freq, voltage = self.calc_freq_and_voltage()
        period = self.get_translen_period(translen)
        self.siggen.config_waveform(freq, voltage)
        self.siggen.config_burst(burst=(rgm.source != 1), cycles=self.args.cycles, period=period)

        self.uuts.abort()

        self.uuts.setup(
            post=post,
            trigger=trigger,
            demux=self.args.demux,
            spad=self.args.spad,
            rgm=rgm,
            translen=self.args.translen
        )

        for shot in self.get_run_shot():

            self.uuts.arm()
            self.uuts.wait_armed()
            print('Ready')

            if trigger.source != 1: self.siggen.trigger(delay=1)
            else: self.uuts.pulse_soft_trigger()
            print('Triggered')

            self.uuts.wait_idle()
            print('Stopped')

            dataset = self.read_transient_data()