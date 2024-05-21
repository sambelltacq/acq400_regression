

#!/usr/bin/env python3

"""Tests uuts High throughput streaming"""


"""
Must be run on hts host
detect AFHABA automatically
init stream program
run for 30 seconds default (change via arg)
save data to local /mnt/regression/data?

import buffers
    check spad no gaps
    check waveform isclose to ideal waveform
    
"""

from acq400_regression.analysis import Waveform

from acq400_regression.tests.generic import generic
from acq400_regression.misc import tri, RThread, backstage, DotDict

from acq400_hapi import PR, pprint #remove me after testing

import numpy as np
from matplotlib import pyplot as plt

import os
import shutil
import time

class Hts(generic):
    test_type = "hts"

    post = 100000

    dir_fmt = "{type}"
    
    def parser(parser):
        print(f"prepost argparser here")
        
    @backstage #rename to be better
    def rtm_t_stream_init(self, lport, nbuffers, concat=1, recycle=0):
        self.log.debug(f"Starting rtm-t-stream-disk on lport {lport}")
        
    def start_streams(self):
        print('start streams')
        self.uuts.afhba_ident()
        for uut in self.uuts:
            for conn in uut.afhba404:
                os.makedirs()
                #make dir for stream here erase old one if exists
                #start stream here
                print(uut)
                print(conn)
            
        
    
    @backstage
    def start_streamer(self, lport, nbuffers, concat=1, recycle=0):
        print('starting streamer')
        #os.removedirs(self.saveroot)
        shutil.rmtree(self.saveroot)
        os.system(f"ls {self.saveroot}")
        os.makedirs(self.saveroot, exist_ok=True)
        env = {
            'RTM_DEVNUM':   lport,
            'NBUFS':        nbuffers,
            'CONCAT':       nbuffers,
            'RECYCLE':      recycle,
            'OUTROOT':      self.saveroot
        }
        envstr = self.th.env_to_str(env)
        exepath = os.path.join(self.AFHBA_DIR, 'STREAM/rtm-t-stream-disk')
        print(f"Running: {envstr} {exepath}")
        os.system(f"{envstr} {exepath} &> /dev/null")
        print(f"Complete: {envstr} {exepath}")
        
    def check_hts_data(self): # make better
        print('checking hts')
        #make file finding automatic
        
        result = DotDict()
        #add import dataset from file
        filepath = os.path.join(self.saveroot,'000001/0.00')
        uutname = 'acq2106_130'
        self.th.import_dataset(uutname, filepath, self.tsamples, self.nchans)
        
        for chan, chan_data in self.th.dataset[uutname]['chans'].items():
            print(f"{chan} {chan_data}")
            break
        
        ideal_wave = Waveform.generate_ideal_wave(
            chan_data, 
            tsamples=self.tsamples,
            wavelength=20000,
            cycles=1,
            eindex=0,
            translen=0,
            soft=True,
            rising=True,
        )
        self.ideal_wave = ideal_wave
            
        tolerance = Waveform.get_tolerance(chan_data, self.args.tolerance)
        sync = np.allclose(ideal_wave, chan_data, atol=tolerance)
        
        result.passed = sync
        self.th.update_subtest('wave_synchronous', uutname, result)
        return sync
    
    
    """
    TODO:
        get afhba connections
        run as many rtm_t streams as required
        handler 2 streams from 1 uut
        attack stream thread to uut object
        save data per unit
        
        dataset['multisource'] = []
        dataset['multisource'] = ['A', 'B']?
        
        uut{
            a: {
                'lport': 0,
                'thread': threadObject,
            }
        }
        hts savedir
            /mnt/hts_test/acq2106_001/A/cycles/lport.01
        
    
    """

    def run(self):
        freq, voltage = self.get_freq_and_voltage()
        self.siggen.config_params(freq, voltage)
        self.siggen.config_contiguous()
        
        #add to arg parser
        self.saveroot = "/mnt/hts_data/"
        self.AFHBA_DIR = "~/PROJECTS/AFHBA404/"
        self.tsamples = 100000
        
        #auto get these values
        lport = 0 #find lport here
        data_size = 2
        self.nchans = 32
        self.np_type = np.int16
        
        size_in_megabytes = (self.nchans * data_size * self.tsamples) / 1000000
        nbuffers = int(-( -size_in_megabytes // 1))
        self.save_state('nbuffers', nbuffers)
        
        self.run_iters(nbuffers, lport)
        
        if self.args.save: self.th.save_test()
        self.th.stash_results()
        
        self.log.info(f"[{self.th.testname.title()}] Test Completed")
        
        
    #@generic.catch_error
    def run_iters(self, nbuffers, lport):
        for run in self.get_run():
            self.log.info(f"[{self.test_type}]")
            results = []
            
            self.start_streams()
            
            exit()
            self.uuts.abort()
            
            rtned = self.start_streamer(lport, nbuffers)
            self.uuts.start_stream()
            self.uuts.wait_armed(timeout=45)
            self.log.info('Ready')
            #trigger here?
            
            rtned.join() #stream done add time out? 
            self.uuts.stop_stream()
            self.log.info('Completed')


            results.append(self.check_hts_data())
            
            if not self.check_passed(results): break
            time.sleep(5)
        self.log.info(f"All runs complete {run}/{self.args.runs}")