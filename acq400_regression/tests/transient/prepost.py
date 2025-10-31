from acq400_regression.tests.test_common import TestCommon
from acq400_regression.arg_parser import ArgTypes

"""
Prepost

Test prepost transient operation and data capture

Usage:
    acq400_regression test prepost acq1001_084 --siggen=SG0106 ---pre=50000 --post=5000 --trigger=1,0,1 --event=1,0,1
"""

class Prepost(TestCommon):

    all_triggers = ["1,0,0", "1,0,1", "1,1,1"]

    all_events = ["1,0,0", "1,0,1"]

    run_params = ['pre', 'post', 'trigger', 'event']

    checks = ['spad', 'synchronous']
    
    @classmethod
    def get_args(cls, parser):
        parser.add_argument('--siggen', help='signal generator hostname', required=True)
        parser.add_argument('--pre', default=50000, type=ArgTypes.list_of_ints, help='Post samples')
        parser.add_argument('--post', default=50000, type=ArgTypes.list_of_ints, help='Post samples')
        parser.add_argument('--trigger', '--triggers', default='all', type=ArgTypes.list_of_trinarys(cls.all_triggers), help='Triggers to test 1,0,0/1,0,1/1,1,1 or all')
        parser.add_argument('--event', '--events', default='all', type=ArgTypes.list_of_trinarys(cls.all_events), help='Events to test 1,0,0/1,0,1 or all')
        return parser

    def start_test(self):      
        for params in self.get_run_parameters():
            self.start_run(**params)

    def start_run(self, pre, post, trigger, event, **kwargs):

        freq, voltage = self.calc_freq_and_voltage()
        self.siggen.config_waveform(freq, voltage)
        self.siggen.config_burst(burst=(event.source != 1), cycles=self.args.cycles)

        self.uuts.abort()

        self.uuts.setup(
            pre=pre,
            post=post,
            trigger=trigger,
            event0=event,
            demux=self.args.demux,
            spad=self.args.spad
        )

        for shot in self.get_run_shot():

            self.uuts.arm()
            self.uuts.wait_armed()
            print('Ready')

            if trigger.source != 1: self.siggen.trigger(delay=1)
            else: self.uuts.pulse_soft_trigger()
            print('Trigger start')

            self.uuts.wait_for_samples(samples=pre)
            print('Pre samples Filled')

            if event.source != 1: self.siggen.trigger(delay=1)
            else: self.uuts.pulse_soft_trigger()
            print('Trigger event')


            self.uuts.wait_idle()
            print('Stopped')

            #TODO fix plotting
            # read and check data
            #dataset = self.controller.read_data()
            #dataset.check_spad0()
            # plot data
            #dataset.plot()
            #if dataset.failed(): break