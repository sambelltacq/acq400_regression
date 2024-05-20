#!/usr/bin/env python3

import importlib
import time
import requests
import os
import json
import argparse

import numpy as np
from matplotlib import pyplot as plt

from acq400_hapi import PR, pprint, acq400_logger
from acq400_regression.uut_handler import uut_handler
from acq400_regression.siggen_handler import siggen_handler
from acq400_regression.misc import DotDict, custom_legend, to_hex


from acq400_regression.custom_parser import get_default_parser

class TestException(Exception):
    def __init__(self, reason):
        super().__init__()

class Test_Handler():
    uuts = None
    siggen = None
    test = None
    parser = get_default_parser()

    args = {}
    dataset = {}
    stored_results = []
    to_be_uploaded = []

    def __init__(self, uutnames: list, args: dict={}):
        self.set_args(args)
        self.init_logger(self.args.get('debug', False))
        self.set_uuts(uutnames)
        self.timestart = self.gen_timestamp()
        self.set_test_dir()
        
    def parser_args(self):
        """
            1)
            get args
            parser known args
            init uuts
            init siggen
            init test dir
            
        
        """
        print('parse args here')
        return 'hello world'
    
    def import_new_args():
        """
        parser
        parser = self.test.get_args(parser)
        args = parser.parser_args()
        self.args combine with args
        
        use custom argparser 
        
        if parser contains 
        
        """
        return None
    
    #Handler init methods
    
    def init_logger(self, debug=False, logfile='regtest.log'):
        level = 0 if debug else 20
        self.log = acq400_logger('acq400_regression', level=level, logfile=logfile)
        self.log.add_new_level('success', 21, color="\033[92m")
        self.log.add_new_level('failure', 22, color="\033[31m")

    def set_uuts(self, uutnames: list):
        self.uuts = uut_handler(uutnames, self.log, self.args.master, self.args.spad)

    def set_args(self, args):
        if type(args) != dict:
            args = vars(args)
        self.args = DotDict(**args)
        
    def gen_timestamp(self):
        fmt = "%y%m%d%H%M%S"
        return time.strftime(fmt)
        
        
        
        
        
    def get_channels(self, uut):
        return self.args.channels if self.args.channels != 'all' else range(1, uut.nchan + 1)
    
    def get_spad(self, uut):
        """returns spad mapped to channel index"""
        factor = 1 if int(uut.s0.data32) else 2
        spadlen = int(uut.s0.spad.split(',')[1])
        spadstart = uut.nchan() - spadlen * factor
        return {spad : spadstart + (spad * factor) for spad in range(spadlen)}
    
    def get_siggen(self):
        if not self.siggen:
            if self.args.has('siggen'):
                self.siggen = siggen_handler(self.args.siggen, self.log)
                PR.Green('connecting siggen')
        return self.siggen
            






    #Data Handling Methods

    def import_dataset(self, source='UUT'):
        """Imports data from source
            source can be UUT or HOST or FILE(TODO)
            raw data stored at hander.dataset[uut].data
            channel pointers at handler.dataset[uut].chan_data
            spad pointers at handler.dataset[uut].spad_data
            
        """
        self.log.info('Offloading data')
        self.dataset = {}
        for uut in self.uuts:#TODO: cleanup
            self.log.debug(f"Importing data data from {uut.hostname}")
            data = DotDict()
            data.data_size = uut.data_size
            data.nchan = uut.nchan()
            
            if source == 'UUT':
                data.data = uut.read_channels()
            elif source == 'HOST':
                data.data = self.read_channels_from_file(uut) #add multi file support          
            
            data.chan_data = {}
            for chan in self.get_channels(uut):
                if chan > uut.nchan(): continue
                data.chan_data[chan] = data.data[chan - 1]
                
            data.spad_data = {}   
            for spad, spadchan in self.get_spad(uut).items():
                chans = [spadchan]
                if uut.data_size == 2:
                    chans.append(spadchan + 1)
                    data.spad_data[spad] = data.data[chans].T.reshape(-1).view(np.uint32)
                elif uut.data_size == 4: #untested
                    data.spad_data[spad] = data.data[chans].view(np.uint32)
            
            data.datalen = len(data.data[0])
            data.es_indexes = self.find_event_signatures(self.to_uint32(data.data))
            
            if self.args.debug:
                pprint(data)
                
            self.dataset[uut.hostname] = data
            
        return self.dataset

    
    
    def read_channels_from_file(self, uut):             
        self.log.debug(f"Importing data from {uut.host_data}")
        #check file exists here
        #add dir support GLOBBING here
        nchan = uut.nchan()
        dtype = np.int32 if int(uut.s0.data32) else np.int16
        remainder = int(os.path.getsize(uut.host_data) / uut.data_size) % nchan
        return np.fromfile(uut.host_data, dtype=dtype)[:-remainder].reshape(-1, nchan).T      
    
    def to_uint32(self, data):
        """Converts data to uint32"""
        if data[0].dtype == np.int16:
            chans32 = int(len(data) / 2)
            return np.squeeze(np.transpose(data.reshape(chans32, 2, -1), axes=(0, 2, 1)).view(np.uint32), axis=-1)
        return data.view(np.uint32)
    
    def find_event_signatures(self, data32):
        """returns event signature indxes"""
        self.log.debug('Finding event signatures in data')
        event_signatures = [
            0xaa55f151,
            0xaa55f152,
            0xaa55f154,
        ]
        for chandata in data32:
            for es in event_signatures:
                indexes = np.where(chandata == es)[0]
                if len(indexes) > 0: return indexes
        return []
    
    def mask_es(self, arrlen, indexes):
        """returns a array mask to exclude es"""
        mask = np.full(arrlen, True)
        if len(indexes) > 0: mask[indexes] = False
        return mask
    
    #data saving and plotting methods 
    
    def save_test(self):
        self.save_dataset()
        self.save_event_signatures()
        self.plot_dataset(plot=False, save=True) #fix me
    
    def plot_dataset(self, plot=True, save=False):
        """Plot all data in dataset"""
        
        self.log.debug("Plotting dataset")
        for uutname, data in self.dataset.items():
            self.log.debug(f"Plotting {uutname}")
            plt.figure(uutname)
            plt.clf()
            plt.gcf().set_size_inches(8, 6)
            plt.title(uutname)
            
            mask = self.mask_es(data.datalen, data.es_indexes)
            
            for chan, data in data.chan_data.items():
                plt.plot(data[mask], label=f"CH{chan}")

            if hasattr(self.test, 'ideal_wave'):
                plt.plot(self.test.ideal_wave, label=f"ideal_wave")
                
            custom_legend(plt)
            
            if save:
                filename = f"{uutname}.{self.test.timestamp}.png"
                savepath = os.path.join(self.get_test_subdir(), filename)
                self.log.info(f"Saving plot to {savepath}")
                plt.savefig(savepath)
        
        if plot:
            self.log.info("Plotting")
            plt.show()

        
    def save_dataset(self):
        """Saves data to file"""
        #TODO filename data chans and spad chans and data type
        #acq1001_001.240101.8CH.8SPD.32BIT.dat
        savedir = self.get_test_subdir()
        for uut, data in self.dataset.items():
            filename = f"{uut}.{self.test.timestamp}.{data.nchan}CH.{data.data_size}B.dat"
            savepath = os.path.join(savedir, filename)
            with open(savepath, 'w') as f:
                self.log.info(f"Saving data to {savepath}")
                data.data.T.tofile(f)
    
    def save_event_signatures(self):
        """Saves event signatures in hex to file"""
        savedir = self.get_test_subdir()
        for uut, data in self.dataset.items():
            if len(data.es_indexes) > 0:
                filename = f"{uut}.{self.test.timestamp}.es"
                savepath = os.path.join(savedir, filename)
                data32 = self.to_uint32(data.data)
                with open(savepath, 'w') as f:
                    self.log.info(f"Saving event signatures to {savepath}")
                    for es in data.es_indexes:
                        f.write(f"[{es}]: {' '.join(list(map(to_hex, data32.T[es])))}\n")
                print(data32.T[data.es_indexes])
        
    
    #file methods
    
    def set_test_dir(self):
        """sets the test dir root/module/timestamp/"""
        modules = [module for module in self.uuts.get_all_modules() if module.startswith('ACQ')]
        most_common_module = max(set(modules), key=modules.count)
        self.log.debug(f"most_common_module {most_common_module}")
        self.dir = os.path.join(self.args.root, most_common_module, self.timestart)

    def get_test_subdir(self):
        subdir = self.test.dir_fmt.format(**self.test.state)
        invalid_chars = [',']
        for char in invalid_chars:
            subdir = subdir.replace(char, '')
        path = os.path.join(self.dir, subdir)
        os.makedirs(path, exist_ok=True)
        return path
    
    
    #run test methods

    def run_tests(self, tests:list):
        """Runs a list of tests"""
        for test in tests:
            self.run_test(test)
        self.log.info("All tests complete")
        if self.args.save: self.results_to_file()
        if self.args.url: self.send_to_remote(self.args.url)
        
    def add_test_args(self):
        """Adds test specific args"""
        if not hasattr(self.testclass, 'get_args'):
            return
        parser = argparse.ArgumentParser(add_help=False)
        self.testclass.get_args(parser)
        args = parser.parse_known_args()[0]
        self.args.update(vars(args))

    def run_test(self, testname):
        self.log.debug(f"Running {testname}")
        self.import_test(testname)
        self.add_test_args()
        self.test = self.testclass(self)
        self.test.run()
        return
        """
        try:
        except Exception as e:
            self.handle_test_error(e)
        """
            
    def import_test(self, testname):
        """Import test from tests dir"""
        self.testname = testname
        self.moduri = f"acq400_regression.tests.{self.testname}"
        self.log.debug(f'Importing test: {self.moduri}')
        self.testmodule = importlib.import_module(self.moduri)
        self.testclass = getattr(self.testmodule, self.testname.title())
        #self.test = getattr(self.testmodule, self.testname.title())(self)
        
    def handle_test_error(self, error):
        self.log.error(f"{self.testname} {error}")
        if self.test:
            self.test.save_state('errored', str(error))
            self.test.save_state('result', 'errored')
            self.stash_results()
            
            
    #result handling methods

    def stash_results(self):
        """Stashes test state and test results"""        
        results = dict(self.test.state)
        if self.test.results:
            results['subtests'] = dict(self.test.results)
        self.test.results.clear()
        #pprint(results)
        self.stored_results.append(results)
        
    def update_subtest(self, testname, uut, results):
        """Stores subtest results"""
        if uut not in self.test.results:
            self.test.results[uut] = {}
        self.test.results[uut][testname] = results
    
    def compile_results(self):
        """combines uut state and test results for saving""" 
        payload = {}
        payload['uuts'] = []
        for uut in self.uuts:
            payload['uuts'].append(uut.config)
        payload['tests'] = self.stored_results
        return payload

    def results_to_file(self):
        """Write uuts config, test state and results to file"""
        compiled = self.compile_results()
        pprint(compiled)
        savepath = os.path.join(self.dir, 'results.json')
        os.makedirs(self.dir, exist_ok=True)
        with open(savepath, 'w') as f:
            json.dump(compiled, f, indent=4)
            self.log.info(f"Results saved to {savepath}")
    
    def send_to_remote(self, url):
        """Send results payload to remote host"""
        self.log.info(f"Results sent to {url}")
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post(self.args.url, data=json.dumps(self.payload), headers=headers)
        self.upload_file(url)
        
    def upload_file(self, url):
        """Upload all files in to be uploaded list to remote server"""

    def env_to_str(self, env): #move to misc
        return ' '.join([f"{k}={v}" for k, v in env.items()])