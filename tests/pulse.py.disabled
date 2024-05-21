
#!/usr/bin/env python3

"""Tests uuts post transient shot"""

from acq400_regression.tests.generic import generic
from acq400_regression.misc import tri

from acq400_hapi import PR, pprint #remove me after testing

import epics

def create_stl():
    stl3 = [
        "0,0x0000",
        "1,0x0101",
        "2,0x0202",
        "3,0x0404",
        "4,0x0808",
        "5,0x1010",
        "6,0x2020",
        "7,0x4040",
        "8,0x8080",
        "9,0x0101",
    ]
    stl3 = [
        "0,0x00000000",
        "1,0xffffffff",
        "2,0x00000000",
    ]
    stl3 = '\n '.join(stl3)
    return stl3    
"""
LOOPBACK acq to DO
check sqaure wave is correct 
stream to file 
check file


##pulse_generator 

DIO IMMEDIATE personality: ACQ1001_TOP_09_6B_32B-DIO.bit.gz 
DIO PG personality: ACQ1001_TOP_09_6B_32B-PG.bit.gz

1) Connect loopback

2) Scripting
    # PROJECTS/acq400_hapi/user_apps/pyepics:
    dio_immediate_pattern.py # continual load of immediate pattern *
    dio_immediate_pattern_using_pg.py # continual load of partial immediate pattern *
    pg_pattern_load.py # one-time load of PG pattern
    # * normally run locally from /mnt/local/DEMO (author uses a VPN, on the LAN, remote will be OK)

3)


?) pattern load

    disable gpg_enable
    set gpg_mode
    enable trigger on site
    set trigger source
    set trigger edge
    gpg_stl put lines of stl
    gpg_pulse_defv set filename
    diable gpg_enable


0,0x0000  # 00000000 00000000
1,0x5555  # 10000000 10000000
2,0x0000  # 00000000 00000000
3,0xaaaa  # 10000000 10000000
4,0x0000 # 00000000 00000000


"""


import time
class Pulse(generic):
    test_type = "pulse"

    post = 100000
    
    dir_fmt = "{type}"
    
    stl = [
        "0,0x00000000",
        "1,0xffffffff",
        "5,0x00000000",
    ]
    
    waveform = 'SQUARE'
    
    def run(self):
        site = 2
        stl = '\n '.join(self.stl)
        
        self.eindex = 1000
        self.translen=4000
        self.wavelength = self.translen * 2
        
        self.uuts.transient(pre=self.pre, post=self.post, trg='1,1,1')
        self.uuts.config_pg(site, stl)
        PR.Green(f"LOAD STL {stl}")
        
        self.uuts.arm()
        self.log.info('Arming')

        self.uuts.wait_armed(timeout=45)
        self.log.info('Ready')
        
        self.uuts.wait_completed(timeout=60)
        self.log.info('Completed')
        
        dataset = self.th.offload_dataset()
        ideal_wave, tolerance, dtype = self.get_ideal_wave(dataset, scale=0.5)
        self.check_wave_synchronous(dataset, ideal_wave, tolerance)
        
        self.th.plot_dataset()
        
        
        exit()
        
        
        
        
        
        
        
        
        
        self.stl = ''.join(self.stl)
        self.stl2 = ''.join(self.stl2)
        stl3 = create_rgm_stl()
        PR.Yellow(stl3)
        PR.Yellow(repr(stl3))
        #stlpv = epics.PV(f"{uut}:{site}:GPG:STL")
        #stlpv.put(self.stl2, wait=True)
        #exit()
        self.uuts.upload_stl(2, stl3)
        exit()
        self.stl = ' '.join(self.stl)
        #self.stl = f"{self.stl}\n"
        print(self.stl)
        print(repr(self.stl))
        self.uuts.upload_stl(2, self.stl)
        
        
        #make gpg function
        #site
        
        
        
        
        
        exit()