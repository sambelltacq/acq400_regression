#!/usr/bin/env python3

from acq400_regression.misc import DotDict, tri, custom_legend, ifnotset
from acq400_regression.analysis import Waveform
import numpy as np

from acq400_hapi import PR, pprint #remove me after testing
import numpy as np
from matplotlib import pyplot as plt

import time
import os

class BaseTest():
    test_type = 'base'

    triggers = [
        [1,0,0],
        [1,0,1],
        [1,1,1],
    ]

    events = [
        [1,0,0],
        [1,0,1],
    ]
    
    pre = 0
    post = 0
    translen = None
    waveform = 'SINE'

    dir_fmt = "{type}_{timestamp}"

    def __init__(self, th):
        self.th = th
        self.args = th.args
        self.uuts = th.uuts
        self.log = th.log
        self.siggen = self.th.get_siggen()
        self.state = DotDict()
        self.results = DotDict()
        self.timestamp = 0

        self.log.info(f"\n[{self.th.testname.title()}] Test Started")

        self.save_state('type', self.test_type)
        self.save_state('channels', self.args.channels)
        self.save_state('tolerance', self.args.tolerance)
        self.save_state('cycles', self.args.cycles)
        
        if self.args.debug: pprint(self.args)

    def catch_error(func):
        """Catches exceptions"""
        PR.Red("catch error start")
        print(func)
        def wrapper(self, *args, **kwargs):
            PR.Yellow('inside Catch error')
            print(self)
            try:
                func(self, *args, **kwargs)
            except Exception as e:
                self.th.handle_test_error(e)
        return wrapper

    def set_timestamp(self):
        self.timestamp = self.th.gen_timestamp()
        self.save_state('timestamp', self.timestamp)

    def get_trigger(self):
        for trigger in self.triggers:
            if self.args.triggers != 'all' and trigger not in self.args.triggers:
                continue
            self.save_state('trigger', tri(trigger))
            yield trigger

    def get_event(self):
        for event in self.events:
            if self.args.events != 'all' and event not in self.args.events:
                continue
            self.save_state('event', tri(event))
            yield event

    def get_run(self):
        self.set_timestamp()
        self.runs = self.args.runs
        for run in range(1, self.runs + 1):
            print()
            self.run = run
            self.log.info(f"Starting run {run}/{self.runs}")
            self.save_state('runs', f"{run}/{self.runs}")
            yield run

    def save_state(self, key, value):
        """Save test state"""
        serializable_types = (int, float, str, bool, list, dict)
        if not isinstance(value, serializable_types):
            self.log.warning(f"converting bad value {type(value)}'{value}'")
            value = str(value)
        self.state[key] = value

    def is_rising(self, *args):
        """Returns true if any trinary has sense rising"""
        return any([tri(t, 'sense') == 1 for t in args])
    
    def is_soft(self, *args):
        """Returns true if any trinary has source soft"""
        return any([tri(t, 'source') == 1 for t in args])

    def get_freq_and_voltage(self, wavelength=None):
        """Gets ideal freq and voltage for siggen"""
        wavelength = ifnotset(wavelength, self.args.wavelength)
        clk = [uut.clk for uut in self.uuts][0]
        freq = clk / wavelength
        voltage = min([uut.voltage for uut in self.uuts])
        self.save_state('freq', freq)
        self.save_state('voltage', voltage)
        return freq, voltage
    
    def get_burst_period(self, factor=1):
        """Retuns burst period of len wavelength * factor in ms"""
        clk = [uut.clk for uut in self.uuts][0] #TODO make nicer
        tlen = self.wavelength * self.args.cycles
        return round(tlen / clk * factor, 2)
    
    #Test methods
    
    def add_removed_es(self, dataset, indices):
        """add removed es into mask"""
        return
        for uutname, data in dataset.items():
            print(f"{uutname} {data.es_indexes}")
            data.es_indexes.extend(indices)
            print(f"{uutname} {data.es_indexes}")
        return
    
    def check_spad(self, dataset, exclude=[]):
        """check spad[0] is contigious"""
        self.log.info('Checking spad')
        results = []
        print(dataset)
        for uutname, data in dataset.items():
            if len(data.spad_data) < 1:
                self.log.info(f"{uutname} No spad")
                continue
            result = DotDict()
            diffs = np.diff(data.spad_data[0])
            mask = self.th.mask_es(len(diffs), exclude)
            passed = np.all(diffs[mask] == 1) #use event mask here to fix missing samples
            if passed:
                self.log.success(f"{uutname} spad[0] is contigious")
                result.spad0_contigious = True
            else:
                self.log.failure(f"{uutname} spad[0] is not contigious")
                result.spad0_contigious = False
                self.save_spad_errors(uutname, diffs)
            results.append(passed)
            self.th.update_subtest('spad', uutname, result) #fix me
        return all(results)
    
    def save_spad_errors(self, uutname, diffs):
        """print and save spad"""
        errors = 5
        jumps = np.where(diffs != 1)
        if len(jumps) < 1: return
        filepath = os.path.join(self.get_test_subdir(), f"{uutname}.jumps")
        with open(filepath, 'w') as fp:
            self.log.debug(f"Writing spad jumps to {filepath}")
            for jump in jumps:
                if self.args.debug and errors > 0:
                    self.log.error(f"SPAD [{jump}]: {diffs[jump]}")
                    errors -= 1
                fp.write(f"[{jump}] {diffs[jump]} \n")
            
            
            
    def check_es(self, dataset, expected_indices=[]):
        """Check the event signatures are at expected indexes"""
        self.log.info('Checking event signatures')
        results = []
        
        for uutname, data in dataset.items():
            result = DotDict()
            passed = np.array_equal(data.es_indexes, expected_indices)
            
            if passed:
                self.log.success(f"{uutname} Event signatures are at expected indexes")
                result.correct_indexes = True
            else:
                self.log.failure(f"{uutname} Event signatures are not at expected indexes")
                result.correct_indexes = False
                
            results.append(passed)
            self.th.update_subtest('event_signature', uutname, result) #fix me   
            
        return all(results)
    
    def check_wave(self, dataset, ideal_wave, tolerance):
        """Compares each channel to an ideal wave generated from known values"""
        self.log.info('Checking wave')
        results = []
        for uutname, data in dataset.items():
            result = DotDict()
            passed = True
            bad_chans = []
            
            mask = self.th.mask_es(len(data.data[0]), data.es_indexes)
            
            for chan, chan_data in data.channels.items():
                sync = np.allclose(chan_data[mask], ideal_wave[mask], atol=tolerance)
 
                if sync:
                    self.log.success(f"{uutname} CH{chan}: in sync with ideal wave")
                else:
                    passed = False
                    bad_chans.append(chan)
                    self.log.failure(f"{uutname} CH{chan}: not in sync with ideal wave")
                    
            results.append(passed)
            
            result.synchronous = passed
            if len(bad_chans) > 0: result.bad_chans = bad_chans
              
            self.th.update_subtest('wave', uutname, result)
        return all(results)
            
    def get_ideal_wave(self, dataset, soft=False, rising=True, scale=None):
        """gets the ideal wave using channel data"""
        self.log.debug(f"Generating ideal wave soft[{soft}] rising[{rising}] scale[{scale}]")
        for uutname, data in dataset.items():
            for chan, chan_data in data.channels.items():
                
                dtype = chan_data.dtype
                tolerance = Waveform.get_tolerance(chan_data, self.args.tolerance)
                """                
                print()
                PR.Yellow(f"tsamples={data.datalen}")
                PR.Yellow(f"wavelength={self.wavelength}")
                PR.Yellow(f"cycles={self.args.cycles}")
                PR.Yellow(f"eindex={self.get_event_indexes()}")
                PR.Yellow(f"translen={self.translen}")"""
                
                ideal_wave = Waveform.generate_ideal_wave(
                    chan_data, 
                    tsamples=self.pre+self.post,
                    #tsamples=data.datalen,
                    wavelength=self.wavelength,
                    cycles=self.args.cycles,
                    eindex=self.get_event_indexes(),
                    translen=self.translen,
                    soft=soft,
                    rising=rising,
                    waveform=self.waveform
                )
                
                self.log.debug(f"dtype {dtype}")
                self.log.debug(f"tolerance {tolerance}")
                if scale:
                    ideal_wave = ideal_wave * scale
                self.ideal_wave = ideal_wave
                return ideal_wave, tolerance, dtype 
        
    def get_event_indexes(self): #fix me
        #gen_expected_indeices
        """Gets event(s) index(s)"""
        if hasattr(self, 'eindex'): return self.eindex
        if not self.translen:
            return self.pre    
        return list(range(0, self.pre+self.post, self.translen))
    
    def check_passed(self, results):
        """handles results array"""
        if all(results):
            self.save_state('result', 'pass')
            self.log.success(f"Run {self.run}/{self.runs} Passed")
            if self.args.plot > 0: self.th.plot_dataset()
            return True
        else:
            self.save_state('result', 'fail')
            self.log.failure(f"Run {self.run}/{self.runs} Failed")
            if self.args.plot: self.th.plot_dataset()
            return False            
            
            
            
            
            
            
            
                
                

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    def run_wave_comparison2_old(self, dataset, soft=False, rising=True):
        self.log.info('Running wave comparison2')
        passed = True
        bad_chans = {}

        ideal_wave, tolerance, dtype = self.get_ideal_from_data2(dataset, soft, rising)

        for uut in dataset:
            bad_chans[uut] = []

            for chan, chan_data in dataset[uut]['chans'].items():
                result = np.allclose(chan_data, ideal_wave, atol=tolerance)
                if result:
                    self.log.success(f"{uut} CH{chan}: Passed wave comparison")
                else:
                    passed = False
                    bad_chans[uut].append(chan)
                    self.log.failure(f"{uut} CH{chan}: Failed wave comparison")

        if 'wave_comparison' in self.results: del self.results.wave_comparison

        for uut, chans in bad_chans.items():
            self.results.wave_comparison[uut].passed = passed
            if len(chans) > 0: self.results.wave_comparison[uut].bad_chans = chans

        return passed
    
    def get_ideal_from_data2_old(self, dataset, soft, rising):
        for uut in dataset:
            for chan, chan_data in dataset[uut]['chans'].items():
                dtype = chan_data.dtype
                tolerance = Waveform.get_tolerance(chan_data, self.args.tolerance)
                if soft:
                    offset = Waveform.get_wave_start_offset(chan_data, self.args.divisor)

                #remove these debugs
                self.log.debug(f"wavelength: {self.args.divisor}")
                self.log.debug(f"pre: {self.pre}")
                self.log.debug(f"post: {self.post}")
                self.log.debug(f"cycles: {self.args.cycles}")
                self.log.debug(f"soft: {soft}")
                self.log.debug(f"rising: {rising}")
                self.log.debug(f"offset: {offset}")

                ideal_wave = Waveform.generate_sine2(
                    length=self.pre + self.post, 
                    wavelength=self.args.divisor,
                    cycles=1,
                    event=0,
                    sense=1,
                    translen=self.args.translen,
                    offset=offset
                )
                self.log.debug(f"dtype {dtype}")
                self.log.debug(f"tolerance {tolerance}")
                self.ideal_wave = ideal_wave
                return ideal_wave, tolerance, dtype
            
            
    def get_ideal_from_data_old(self, dataset, soft, rising):
        for uut in dataset:
            for chan, chan_data in dataset[uut]['chans'].items():
                dtype = chan_data.dtype
                tolerance = Waveform.get_tolerance(chan_data, self.args.tolerance)

                #remove these debugs
                self.log.debug(f"wavelength: {self.args.divisor}")
                self.log.debug(f"pre: {self.pre}")
                self.log.debug(f"post: {self.post}")
                self.log.debug(f"cycles: {self.args.cycles}")
                self.log.debug(f"soft: {soft}")
                self.log.debug(f"rising: {rising}")

                ideal_wave = Waveform.get_ideal_wave(
                    chan_data, 
                    wavelength=self.args.divisor, 
                    pre=self.pre,
                    post=self.post,
                    cycles=self.args.cycles,
                    soft=soft,
                    rising=rising
                )
                self.log.debug(f"dtype {dtype}")
                self.log.debug(f"tolerance {tolerance}")
                self.ideal_wave = ideal_wave
                return ideal_wave, tolerance, dtype     
            