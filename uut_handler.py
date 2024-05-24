#!/usr/bin/env python3

"""uut handler

inits hapi connections to each uut
provides methods for mass getting and setting knobs
"""

import acq400_hapi
import time
import re
from acq400_regression.misc import tri, RThread, all_uuts, DotDict, ifnotset
from acq400_hapi import PR, pprint, pv, STATE, AcqPorts


import socket
import os
import sys
import numpy as np
from matplotlib import pyplot as plt


class uut_handler():

    def __init__(self, hostnames, log, master=None, spad='0,0,0'):
        self.log = log
        self.conns = {}
        self.hostnames = hostnames
        master = master if master else hostnames[0]
        
        for uutname in hostnames:
            self.log.info(f"Init {uutname}")

            uut = acq400_hapi.factory(uutname)
            uut.hostname = uutname
            uut.is_master = False

            uut.s0.spad = spad 
            uut.s0.run0 = f"{uut.s0.sites} {spad}"
            
            if uutname == master:
                log.debug(f"{uutname} is master")
                self.master = uutname
                uut.is_master = True

            #methods to log state
            uut.clk = self.get_clk(uut)
            uut.voltage = self.get_voltage(uut)
            uut.data_size = 4 if int(uut.s0.data32) else 2
            uut.wr = self.get_wr(uut) #make better
            uut.spadlen = self.get_spad(uut)
            
            
            uut.config = self.get_config(uut)
            
            
            #pprint(uut.config)
            self.update_shots(uut) #remove me?
            self.conns[uutname] = uut
            
    def __getitem__(self, key):
        """uuts[hostname/index] helper"""
        if isinstance(key, int):
            return self.conns[self.hostnames[key]]
        return self.conns[key]
    
    def __iter__(self):
        """allows looping over uuts"""
        for uutname in self.conns:
            yield self.conns[uutname]

    def get_all_modules(self):
        """gets all modules"""
        return [modules['model'].split(' ')[0] for name, uut in self.conns.items() for modules in uut.config['modules']]
    
    def split_data_string(self, s):
        """splits key=value pairs into dict"""
        return dict((k, int(v)) if v.isdigit() else (k, v) for k,v in (p.split("=") for p in s.split(' ')))
    
    def get_clk(self, uut):
        """gets the clk from uut"""
        if uut.s1.MODEL.startswith("ACQ43"):
            self.log.debug(f"ACQ43X detected using alternate clk")
            clk = int(float(pv(uut.s1.ACQ43X_SAMPLE_RATE)))
        else:
            clk = int(float(pv(uut.s0.SIG_CLK_S1_FREQ)))
        if not clk:
            self.log.critical(f"{uut.hostname} Clk invalid {uut.clk}")
            exit(1)
        if hasattr(uut.s1, 'ACQ480_FPGA_DECIM'):
            decim = int(pv(uut.s1.ACQ480_FPGA_DECIM))
            clk  = int(clk  / decim)
        self.log.debug(f"{uut.hostname} clk: {clk}")
        return clk

    def get_voltage(self, uut):
        """gets the max voltage of the uut"""
        volt_patt = re.compile(r'([.\d]+)V')
        voltage = 10
        part_num = uut.s1.PART_NUM 
        #can sites have different voltages
        match = re.search(volt_patt, part_num)
        if match:
            voltage = float(match.group(1))
        else:
            if part_num.startswith("ACQ48"):
                voltage = 2.5
        self.log.debug(f"{uut.hostname} {voltage}V")
        return voltage
    
    def get_wr(self, uut):
        """Checks if WR is enabled"""
        try:
            uut.cC.Si5326_TUNEPHASE_OK
            return True
        except:
            return False
        
    def get_spad(self, uut):
        """Returns spad len and spad channels"""
        factor = 1 if int(uut.s0.data32) else 2
        chans = int(uut.s0.spad.split(',')[1])
        return (chans, chans * factor)
    
    def get_config(self, uut):
        """compiles current uut configuration into dict"""
        software_version = uut.s0.software_version
        fpga_version = uut.s0.fpga_version
        config = {
            'uut_name'       : uut.hostname,
            'fpga'           : fpga_version.split(' ')[0],
            'fpga_timestamp' : fpga_version.split(' ')[-1],
            'version'        : int(software_version.split('-')[1]),
            'firmware'       : software_version,
            'serial'         : uut.s0.SERIAL,
            'model'          : uut.s0.MODEL,
            'clk'            : uut.clk,
            'nchan'          : uut.nchan(),
            'spad'           : uut.s0.spad,
            'data_size'      : uut.data_size,
            'master'         : uut.is_master,
            'wr'             : uut.wr,
            'modules'        : [],
        }
        for site in [1,2,3,4,5,6]:
            try:
                module = {}
                module['location'] = site
                module['model'] = uut[site].MODEL
                module['serial'] = uut[site].SERIAL
                module['nchan'] = int(uut[site].NCHAN)
                module['full_model'] = uut[site].PART_NUM
                config['modules'].append(module)
            except KeyError:
                continue
        return config
    
    def state_eq(self, uut, state):
        if uut.statmon.get_state() == state:
            return True
        return False

    def state_not(self, uut, state):
        if uut.statmon.get_state() != state:
            return True
        return False

    def get_knob(self, site, knob):
        return self.knob(site, knob)
    
    def set_knob(self, site, knob, value):
        return self.knob(site, knob, value)

    def knob(self, site, knob, value=None):
        values = {}
        for uutname, uut in self.conns.items():
            try:
                if value: setattr(getattr(uut, site), knob, value)
                values[uutname] = getattr(getattr(uut, site), knob)
            except:
                values[uutname] = None
                self.log.error(f"knob [{uutname} {site} {knob}] invalid")
        return values
    
    def update_shots(self, uut):
        uut.shot = int(uut.s1.shot)
        uut.completed_shot = int(uut.s1.completed_shot)
        self.log.debug(f"{uut.hostname} shot: {uut.shot} completed_shot: {uut.completed_shot}")
        
    def afhba_ident(self):
        """Identify afhba connections and add to uuts"""
        #TODO make afhba handler class?
        class dictclean(dict):
            
            def __getattr__(self, attr):
                print(f"[DotDict] __getattr__ {attr}")
                if attr == 'c':
                    return self
                #return self[attr]
                raise Exception('test1')

                

        d1 = {
            'hello': 'world'    
        }
        d2 = dictclean(d1)
        
        d2.c.key1.key1 = 'value1'
        
        print(d2)
        
        exit()
        
        
        
        
        from acq400_hapi.afhba404 import get_connections
        afhba_cons = get_connections()
        for uut in self: uut.afhba404 = {}
            
        for conn in afhba_cons.values():
            afhba404 = self[conn.uut].afhba404
            afhba404[conn.cx] = DotDict()
            afhba404[conn.cx]['rpot'] = conn.dev
            afhba404[conn.cx]['lport'] = conn.dev
            afhba404[conn.cx]['stream'] = None
            afhba404[conn.cx]['saveroot'] = f"/mnt/hts/{conn.uut}/{conn.cx}"
            t0 = time.time()
            print(afhba404[conn.cx].has('hello'))
            print(f"total {time.time() - t0}")
            
            exit()

    
    
    
    
    
    #async functions
    @all_uuts
    def run0(self, uut):
        self.log.debug(f"Run0 {uut.hostname}")
        uut.s0.run0

    @all_uuts
    def abort(self, uut):
        if self.state_not(uut, STATE.IDLE):
            self.log.debug(f"Aborting {uut.hostname}")
            uut.s0.set_abort
            uut.s0.CONTINUOUS = 0
            time.sleep(5)
        exit()

    @all_uuts
    def arm(self, uut):
        self.log.debug(f"Arming {uut.hostname}")
        self.update_shots(uut)
        uut.s0.set_arm = 1

    @all_uuts
    def start_stream(self, uut):
        PR.Red('Start stream')
        self.update_shots(uut)
        uut.s0.CONTINUOUS = 1 
    
    @all_uuts 
    def stop_stream(self, uut):
        PR.Red('Stop stream')
        uut.s0.CONTINUOUS = 0
        
    @all_uuts
    def stream_data(self, uut):
        print(f'starting stream for {uut.hostname}')
        
    @all_uuts #@dio_uuts has dio has 
    def config_pg(self, uut, site, stl, trg="1,1,1", timescale=10000, mode="LOOPWAIT", name='stl name'):
        self.log.info(f"Configuring PG on {uut} site: {site}")
        uut[site].gpg_enable = 0
        uut[site].gpg_mode = mode
        uut[site].GPG_PULSE_DEF = name
        uut[site].gpg_trg = tri(trg)
        uut.load_dio482pg(site, stl)
        uut[site].gpg_enable = 1
        
    @all_uuts
    def wait_armed(self, uut, timeout=None):
        t0 = time.time()
        while True:
            if int(uut.s1.shot) > uut.shot:
                self.log.debug(f"{uut.hostname} armed")
                break
            self.log.debug(f"{uut.hostname} wait for arm")
            if timeout and time.time() - t0 > timeout:
                self.log.debug(f"{uut.hostname} wait armed exceeded timeout")
                #return self.timeout()
                return Exception('Wait armed exceeded timeout')
            time.sleep(0.5)

    @all_uuts
    def wait_completed(self, uut, timeout=None):
        t0 = time.time()
        while True:
            if int(uut.s1.completed_shot) > uut.completed_shot:
                self.log.debug(f"{uut.hostname} stopped")
                break
            self.log.debug(f"{uut.hostname} wait for stop")
            if timeout and time.time() - t0 > timeout:
                self.log.debug(f"{uut.hostname} wait completed exceeded timeout")
                #return self.timeout()
                return Exception('Wait completed exceeded timeout')
            time.sleep(0.5)

    @all_uuts
    def wait_pre_complete(self, uut, target):
        while True:
            elapsed = uut.statmon.get_elapsed() / uut.nchan()
            if elapsed > target:
                self.log.debug(f"{uut.hostname} pre complete {elapsed}/{target}")
                time.sleep(2)
                break
            self.log.debug(f"{uut.hostname} pre wait {elapsed}/{target}")
            time.sleep(0.5)

    @all_uuts
    def setup(
        self,
        uut,
        pre=0,
        post=0,
        trg='0,0,0',#
        evt='0,0,0',
        evt2='0,0,0',
        rgm='0,0,0',
        soft=None,
        translen=0,
        demux=0,
        ):
        """Configures uut"""
        soft = soft if soft else int(tri(trg, 'source') == 1)
        uut.s0.transient = f"PRE={pre} POST={post} SOFT_TRIGGER={soft} DEMUX={demux}"
        uut.s1.trg = tri(trg)
        uut.s1.event0 = tri(evt)
        uut.s1.event1 = tri(evt2)
        uut.s1.rgm = tri(rgm)
        uut.s1.RTM_TRANSLEN = translen
        
        if not uut.is_master:
            uut.s1.trg = tri(trg, 'source', 0) if trg else '0,0,0'
        time.sleep(1)
    
    @all_uuts 
    def spad(self, uut, spad):
        uut.s0.spad = tri(spad)
        uut.s0.run0 = f"{uut.s0.sites}"
        uut.s0.run0 = f"{uut.s0.sites} {tri(spad)}"
        time.sleep(1)

    @all_uuts
    def stream_to_host(self, uut, blen=4096, runtime=5, max_bytes=None):
        """Stream data from the uut to a file on the host"""
        
        #TODO: make stream status text display here

        uut.host_data = f"{uut.hostname}.stream.temp"
        buffer = bytearray(blen * uut.data_size)
        view = memoryview(buffer).cast('B')
        
        self.log.debug(f"Streaming from {uut.hostname} to {uut.host_data} for {runtime}s")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((uut.hostname, AcqPorts.STREAM))
            
            with open(uut.host_data, "wb") as fp:
                
                time_start = 0
                total_bytes = 0
                while True:
                    
                    nbytes = sock.recv_into(view)
                    
                    if time_start == 0:
                        self.log.info(f"{uut.hostname} Started")
                        time_start = time.time()
                    total_bytes += nbytes              
                    
                    if nbytes == 0:
                        self.log.error(f"{uut.hostname} stream stopped from UUT")
                        break
                    
                    fp.write(buffer[:nbytes])
                    
                    if runtime and not max_bytes and time.time() - time_start > runtime:
                        self.log.info(f"Reached max runtime ")
                        break
                    
                    if max_bytes and total_bytes >= max_bytes:
                        self.log.info(f"Reached max bytes")
                        break
                    
                fp.flush()
            sock.shutdown(socket.SHUT_RDWR)
                    
        self.log.info(f"{uut.hostname} Complete {total_bytes} Bytes")
                    
                    
    
                    
    def stream_to_host_hts(self, uut):
        pass