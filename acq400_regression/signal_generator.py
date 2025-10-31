
from acq400_hapi import Agilent33210A
import logging
import time

#TODO REDO THIS ENTIRE THING
class SignalGenerator(Agilent33210A):
    
    def __init__(self, hostname):
        self.hostname = hostname
        super().__init__(hostname)
        self.send('OUTP:STAT ON')

    def send(self, str):
        #logging.info(f"A33210:{self.ipaddr} > {str}")
        self.socket.send("{}\n".format(str).encode())

    def trigger(self, delay=1):
        """Triggers siggen with optional delay"""
        time.sleep(delay)
        logging.debug(f"Triggering {self.hostname}")
        super().trigger()

    def config(
        freq = 50,
        voltage = 10,
        func = 'SIN',
        burst = True,
        burst_period = 1,
    ):
        pass





    # remove outdated methods below

    def config_waveform(self, freq, voltage, shape='SIN'):
        """Configures output waveform"""
        logging.debug(f"config_waveform {freq}Hz {voltage}V {shape}")
        self.send(f"FREQ {freq}")
        self.send(f"VOLT {voltage}")
        self.send(f"FUNC:SHAP {shape}")
        self.send('OUTP:SYNC ON')

    def config_burst(self, burst=True, cycles=1, period=None):
        """Configures burst"""
        logging.debug(f"config_burst Burst: {burst} {cycles} cycles {period}s")
        if burst:
            self.send('BURS:STAT ON')
            self.send(f"BURS:NCYC {cycles}")
            self.send('TRIG:SOUR BUS')
            if period:
                self.send(f"BURS:INT:PER {period}")
                self.send("TRIG:SOUR IMM")
        else:
            self.send('BURS:STAT OFF')
            self.send('TRIG:SOUR IMM')

    def config_rgm(self, rgm, cycles=1, period=None):
        #TODO: calculate and set correct burst period here 
        #translen ~ clk = correct burst period?
        self.send("BURS:STAT ON")
        if period:
            self.send(f"BURS:INT:PER {period}")
        self.send(f"BURS:NCYC {cycles}")
        self.send("TRIG:SOUR IMM")
        # "clk": 1M translen 25000
        #translen 0.5M

    def config_dc(self, voltage=1):
        logging.debug(f"config_dc: {voltage}V")
        voltage /= 2
        self.send("SOUR:FUNC DC")
        self.send(f"SOUR:VOLT:LEV:IMM:OFFS {voltage}")



# old and busted
    def config_params(self, freq, voltage, shape='SIN'):
        self.send(f"FREQ {freq}")
        self.send(f"VOLT {voltage}")
        self.send(f"FUNC:SHAP {shape}")
        self.send('OUTP:SYNC ON')


    def config_trigger(self, trigger, cycles=1):
        if trigger.source != 1:
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

    def config_rgm(self, rgm, cycles=1, period=None):
        #TODO: calculate and set correct burst period here 
        #translen ~ clk = correct burst period?
        self.send("BURS:STAT ON")
        if period:
            self.send(f"BURS:INT:PER {period}")
        self.send(f"BURS:NCYC {cycles}")
        self.send("TRIG:SOUR IMM")
        # "clk": 1M translen 25000
        #translen 0.5M
        
    def config_contiguous(self):
        self.send('BURS:STAT OFF')
        self.send('TRIG:SOUR IMM')
        
    def enable_free_running_burst(self, cycles=1, period=0.2):
        self.send('TRIG:SOUR EXT')
        
        self.send('BURS:STAT OFF')
        self.send('TRIG:SOUR IMM')
        return
        self.send('BURS:STAT ON')
        self.send(f"BURS:NCYC {cycles}")
        self.send(f"BURS:INT:PER {period}")
        
    def start_free_running_burst(self):
        self.send('TRIG:SOUR IMM')
        
        