#!/usr/bin/env python3


from acq400_hapi import Agilent33210A
from acq400_regression.misc import tri
import time

class siggen_handler(Agilent33210A):

    def __init__(self, hostname, log):
        self.log = log
        self.hostname = hostname
        super().__init__(hostname)
        self.send('OUTP:STAT ON')

    def trigger(self, delay=0):
        """Triggers siggen with optional delay"""
        time.sleep(delay)
        self.log.info(f"Triggering {self.hostname}")
        super().trigger()

    def config_params(self, freq, voltage, shape='SIN'):
        self.send(f"FREQ {freq}")
        self.send(f"VOLT {voltage}")
        self.send(f"FUNC:SHAP {shape}")
        self.send('OUTP:SYNC ON')

    def config_trigger(self, trigger, cycles=1):
        if tri(trigger, 'source') != 1:
            self.send('BURS:STAT ON')
            self.send(f"BURS:NCYC {cycles}")
            self.send('TRIG:SOUR BUS')
        else:
            self.send('BURS:STAT OFF')
            self.send('TRIG:SOUR IMM')

    def config_event(self, event, cycles=1):
        return # unneeded probably! DELETE ME
        if tri(event, 'source') != 1:
            self.send('BURS:STAT ON')
            self.send(f"BURS:NCYC {cycles}")
            self.send('TRIG:SOUR BUS')

    def config_rgm(self, rgm, cycles=1):
        #TODO: calculate and set correct burst period here 
        #translen ~ clk = correct burst period?
        self.send("BURS:STAT ON")
        #self.send("BURS:INT:PER 0.1") #in seconds
        self.send(f"BURS:NCYC {cycles}")
        self.send("TRIG:SOUR IMM")
        
    def config_contiguous(self):
        self.send('BURS:STAT OFF')
        self.send('TRIG:SOUR IMM')
        
    def enable_free_running_burst(self, cycles=1, period=0.2):
        self.send('TRIG:SOUR EXT')
        self.send('BURS:STAT ON')
        self.send(f"BURS:NCYC {cycles}")
        self.send(f"BURS:INT:PER {period}")
        
    def start_free_running_burst(self):
        self.send('TRIG:SOUR IMM')
        
        
        
    

