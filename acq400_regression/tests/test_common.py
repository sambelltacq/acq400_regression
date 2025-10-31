from itertools import product
import logging

from acq400_regression.signal_generator import SignalGenerator
from acq400_regression.data_handler import Dataset

class TestCommon:

    name_fmt = "{test_type}_{timestamp}"
    dat_fmt = "{uutname}.{timestamp}.{tag}.dat"
    png_fmt = "{uutname}.{timestamp}.png"

    run_params = []
    checks = []

    def __init__(self, args, uuts, controller):
        self.args = args
        self.uuts = uuts
        self.controller = controller
        self.test_name = self.__class__.__name__
        self.siggen = SignalGenerator(args.siggen) if hasattr(args, 'siggen') else None

    def get_run_parameters(self):
        """yields all run parameter combinations"""
        keys = []
        values_lists = []

        for run_param in sorted(self.run_params):
            keys.append(run_param)
            run_value = getattr(self.args, run_param, None)

            if run_value is None:
                values_lists.append([None])
            elif isinstance(run_value, (list, tuple)):
                values_lists.append(list(run_value))
            else:
                values_lists.append([run_value])
        try:
            for idx, combo_values in enumerate(product(*values_lists)):
                combo = {k: v for k, v in zip(keys, combo_values)}
                self.curent_run = idx
                self.print_line()
                logging.info(f"[{self.test_name}][Run {self.curent_run}] {self.args.shots} Shots")
                for key, value in combo.items():
                    logging.info(f"- {key}: {value}")
                    #TODO save run parmas here

                yield combo
        finally:
            print('all test parameters are complete')
            #TODO save to disk here


    def get_run_shot(self):
        completed = False
        try:
            for shot in range(1, self.args.shots + 1):
                logging.info(f"[{self.test_name}][Run {self.curent_run}] Shot ({shot}/{self.args.shots})")
                yield shot
            completed = True
        finally:
            if completed:
                logging.info(f"Run completed {shot}/{self.args.shots} Shots\n")
            else:
                logging.error(f"Run failed {shot}/{self.args.shots} Shots\n")
            #TODO save run results here

    def print_line(self):
        print(f"{'-'*70}")

    def calc_freq_and_voltage(self):
        sample_rate = self.uuts[self.uuts.master].get_sample_rate()
        vmax = self.uuts[self.uuts.master].get_module_vmax()
        freq = sample_rate / self.args.wavelength
        logging.debug(f"calc_freq_and_voltage {freq}Hz {vmax}V")
        return freq, vmax

    def get_translen_period(self, translen):
        #TODO take into account the number of waveform cycles?
        sample_rate = self.uuts[self.uuts.master].get_sample_rate()
        period = translen * 1.5 / sample_rate
        logging.debug(f"get_translen_period {period}ms")
        return period

    def read_transient_data(self):
        dataset = Dataset(self.uuts)
        dataset.import_data()
        return dataset
