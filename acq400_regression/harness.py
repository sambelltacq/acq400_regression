
from acq400_hapi import factory, STATE, pv
import logging
import time
import re
import threading
from acq400_regression.utilities import RThread, DotDict
import numpy as np
from pprint import pprint


class UUTWrapper():
    """Custom wrapper around acq400_hapi"""
    def __init__(self, hostname):
        self.hostname = hostname
        self._obj = factory(hostname)

    def __getattr__(self, name):
        return getattr(self._obj, name)

    def __getitem__(self, key):
        return self._obj[key]

    def state_eq(self, state):
        """Check if UUT state equals"""
        #TODO replace with cstate if statmon proves unreliable
        if self.statmon.get_state() == state:
            return True
        return False

    def state_not(self, state):
        """Check if UUT not equals"""
        #TODO replace with cstate if statmon proves unreliable
        if self.statmon.get_state() != state:
            return True
        return False

    def has_wr(self):
        try: return self.s0.has_wr != "none"
        except: return False

    def get_role(self):
        return self.s0.sync_role.split(' ')[0]

    def is_master(self):
        #TODO handle master, fpmaster and rpmaster
        return self.get_role().lower() == 'master'

    def get_configuration(self):
        """ returns uut configuration """
        #TODO Get packages from web
        software_version = self.s0.software_version
        fpga_version = self.s0.fpga_version
        config = {
            'uutname'        : self.hostname,
            'fpga'           : fpga_version.split(' ')[0],
            'fpga_timestamp' : fpga_version.split(' ')[-1],
            'version'        : int(software_version.split('-')[1]),
            'firmware'       : software_version,
            'serial'         : self.s0.SERIAL,
            'model'          : self.s0.MODEL,
            'role'           : self.get_role(),
            'wr'             : self.has_wr(),
            'modules'        : [],
        }
        for site in [1, 2, 3, 4, 5, 6]:
            try:
                module = {}
                module['site'] = site
                module['model'] = self[site].MODEL.split(' ')[0]
                module['full_model'] = self[site].PART_NUM
                module['serial'] = self[site].SERIAL
                module['chans'] = int(self[site].active_chan)
                module['data_size'] = 2 if int(self[site].data32) == 0 else 4
                config['modules'].append(module)
            except KeyError:
                continue

        return config

    def setup(
        self,
        pre=0,
        post=0,
        trigger='0,0,0',
        event0='0,0,0',
        event1='0,0,0',
        rgm='0,0,0',
        spad=None,
        translen=0,
        demux=0,
        stream_mask=0x0,
        ):
        """Configures uut for capture"""
        #Never use SOFT_TRIGGER=1 !
        self.s0.transient = f"PRE={pre} POST={post} SOFT_TRIGGER=0 DEMUX={demux}"
        self.s1.trg = trigger
        self.s1.event0 = event0
        self.s1.event1 = event1
        self.s1.rgm = rgm
        #TODO figure out which translen knob is the correct one
        #uut.s1.rtm_translen = translen
        self.s1.RTM_TRANSLEN = translen
        #TODO handle stream mask here

        if spad: self.s0.spad = spad

        if not self.is_master() and trigger != '0,0,0':
            self.s1.trg = trigger.override('source', 0)

        self.s0.run0 = f"{self.s0.sites} {self.s0.spad}"

    def abort(self):
        """Abort UUT"""
        logging.debug(f"Aborting {self.hostname}")
        self.s0.set_abort = 1
        self.s0.CONTINUOUS = 0

    def arm(self):
        """Arm UUT"""
        logging.debug(f"Arming {self.hostname}")
        self.s0.set_arm = 1

    def wait_armed(self, timeout=45):
        """Wait for state == ARM or timeout"""
        #This will break with AUTO_SOFT_TRIGGER
        t0 = time.time()
        while self.state_not(STATE.ARM):
            logging.debug(f"{self.hostname} wait for ARM")
            if timeout and time.time() - t0 > timeout: raise TimeoutError(f'{self.hostname} failed to reach ARM')
            time.sleep(1)
        logging.debug(f"{self.hostname} ARM")

    def wait_idle(self, timeout=45):
        """Wait for state == IDLE or timeout"""
        t0 = time.time()
        while self.state_not(STATE.IDLE):
            logging.debug(f"{self.hostname} wait for IDLE")
            if timeout and time.time() - t0 > timeout: raise TimeoutError(f'{self.hostname} failed to reach IDLE')
            time.sleep(1)
        logging.debug(f"{self.hostname} IDLE")

    def wait_for_samples(self, samples, timeout=None):
        """Waits until n samples or timeout"""
        t0 = time.time()
        while True:
            current_samples = int(pv(self.s0.CONTINUOUS_SC))
            logging.debug(f"{self.hostname} wait for sample [{current_samples} / {samples}]")
            if current_samples >= samples: break
            if timeout and time.time() - t0 > timeout: return TimeoutError(f'{self.hostname} failed to reach sample target')
            time.sleep(1)

    def get_sample_rate(self, site=1):
        """return sample rate"""

        #TODO Add logging to this method
        try: return int(float(pv(self[site].ACQ43X_SAMPLE_RATE)))
        except: pass

        try: return int(float(pv(self[site].ACQ480_OSR)))
        except: pass

        clk = int(float(pv(self.s0.SIG_CLK_MB_SET)))
        div = int(float(pv(self[site].CLKDIV)))
        return clk // div


    def get_module_vmax(self, site=1):
        #TODO this needs to handle gains properly
        #TODO test with every module type
        voltage = 10
        model = self[site].PART_NUM.split(' ')[0]
        if model.startswith("ACQ48"): voltage = 2.5
        if model.find('2V5') >= 0: voltage = 2.5
        match = re.search('([.\d]+)V', model)
        if match: voltage = int(match.group(1))
        logging.debug(f"{self.hostname}:{site}({model}) Vmax = {voltage}V")
        return voltage

    def pulse_soft_trigger(self, delay=1):
        time.sleep(delay)
        logging.debug(f"Soft Triggering {self.hostname}")
        #TODO: only trigger if master?
        self.s0.soft_trigger = 1

    def get_calibration(self, uut):
        """Return calibration values for every channel"""
        #TODO: what to do if cal returns None?
        eslo = []
        eoff = []
        for site in [1, 2, 3, 4, 5, 6]:
            try: 
                eslo.extend(map(float, uut[site].AI_CAL_ESLO.split(" ")[3:]))
                eoff.extend(map(float, uut[site].AI_CAL_EOFF.split(" ")[3:]))
            except: pass
        return list(zip(eslo, eoff))

    def chan_to_volts(self, chan_data,  eslo, eoff):
        """Return channel scaled to volts"""
        return (chan_data * eslo) + eoff


    def set_stream_mask(self, mask:list):
        """get stream subset mask channels"""

        def ajust_to_16bit(mask):
            new_mask = []
            spadstart = int(self.s0.spadstart) // 2
            for chan in mask:
                offset = chan - spadstart - 1
                if chan <= spadstart: new_mask.append(chan)
                else: new_mask.extend([chan + offset, chan + offset + 1])
            return new_mask

        if int(self.s0.data32) == 0: mask = ajust_to_16bit(mask)
        hex_val = hex(sum(1 << (int(chan) - 1) for chan in mask))
        if len(mask) == 0: hex_val = "none"
        self.s0.stream_subset_mask = hex_val
        logging.debug(f"{self.hostname} set stream subset mask:  {hex_val} {mask}")

    def get_stream_mask(self):
        """get stream subset mask channels"""

        def ajust_from_16bit(mask):
            new_mask = []
            spadstart = int(self.s0.spadstart) // 2
            for chan in mask:
                offset = (chan - spadstart) // 2
                if chan <= spadstart: new_mask.append(chan)
                elif chan % 2 == 0: new_mask.append(chan - offset)
            return new_mask
        try: mask = self.s0.stream_subset_mask
        except: return []
        if mask == 'none': return []
        if mask.startswith("0x"):
            mask = int(mask, 16)
            mask = [i + 1 for i in range(mask.bit_length()) if mask & (1 << i)]
        else:
            mask = list(map(int, mask.split(',')))
        if int(self.s0.data32) == 0: mask = ajust_from_16bit(mask)
        return mask

    def get_continuous_format(self):
        """get continuous data sample format object"""
        mask = self.get_stream_mask()
        return self.get_sample_format(mask)

    def get_transient_format(self):
        """get transient sample data format object"""
        return self.get_sample_format()

    def get_sample_format(self, mask=None):
        """get sample data format object"""
        demuxed = int(self.s0.raw_data_size) == 0 and mask == []

        ssb = int(self.s0.ssb)
        spad_size = 4
        data_size = 4 if int(self.s0.data32) else 2
        spadstart = int(self.s0.spadstart)
        nchan = spadstart // data_size + (ssb - spadstart) // spad_size
        has_mask = mask != None and len(mask) > 0
        chans = sorted(mask if has_mask else list(range(1, nchan + 1)))
        
        data_chans = [chan for chan in chans if chan <= spadstart // data_size]
        data_nchan = len(data_chans)
        data_bytes = data_nchan * data_size
        
        spad_chans = [chan for chan in chans if chan > spadstart // data_size]
        if demuxed: spad_chans = []
        if data_size == 2: spad_chans = spad_chans[:len(spad_chans)]
        spad_nchan = len(spad_chans)
        spad_bytes = spad_nchan * spad_size

        dtype = []
        for chan in data_chans:
            dtype.append((str(chan), np.int16 if data_size == 2 else np.int32))

        for chan in spad_chans:
            dtype.append((str(chan), np.uint32))

        #TODO need to handle DIO use 1b in tag for 1 bit and use uint8 for the array

        tag = "{}CHx{}B+{}SPD".format(data_nchan, data_size, spad_nchan)

        sample_format = {
            'sample_bytes': data_bytes + spad_bytes,    # width of sample

            'data_bytes': data_bytes,                   # size of all data channels
            'data_size': data_size,                     # size of data channel
            'data_chans': data_chans,                   # data channels nums
            'data_nchan': data_nchan,                   # data total channels

            'spad_bytes': spad_bytes,                   # size of all spad channels
            'spad_size': spad_size,                     # size of spad channel
            'spad_chans': spad_chans,                   # spad channels nums
            'spad_nchan': spad_nchan,                   # spad total channels

            'dtype' : dtype,                            # custom dtype
            'tag'   : tag,                              # format tag
        }
        return DotDict(sample_format)


















class UUTCollection():
    """Control a colection of uuts"""
    def __init__(self, hostnames):
        self.uuts = {}
        self.hostnames = hostnames


        self.master = hostnames[0]
        #TODO self.masters = self.find_master()

        if hostnames:
            for hostname in hostnames:
                self.add_device(hostname)

    def find_master(self):
        """handle configing master + slave when multiple uuts are specified"""
        """
        --master=uut
        --rpmaster=uut
        --fpmaster=uut
        or
        --master=fpmaster,uut
        --mrole=master,uut

        Check each uuts role
        if only one master and reset are slaves then set the master from the role
        if no slave or master check which one has HDMi out and sync role master it
            uut.s0.sync_out_cable_det = 1 = master
                how to handle chain when not acq2206?
                    wait for user input to specify master
                        input("Unable to auto detect master enter hostname: ")
            then sync role all others as slave
        sync_role {fpmaster|rpmaster|master|slave|solo}
        rpmaster means trigger in from hdmi; changes sync page
        fpmaster means clk and trigger come in the front panel
        master means 
        slave is slave
        solo should be become either master or slave; what is solo?
        how to handle multiple masters?
            self.master should be an array
                change all methods to support this
            each master must have at least one slave or warn?
        check sync role has set routing as expected
        """
    
    def add_device(self, hostname):
        if hostname in self.uuts:
            raise ValueError(f"Device {hostname} already exists in collection")
        self.uuts[hostname] = UUTWrapper(hostname)
    
    def get_device(self, hostname):
        if hostname not in self.uuts:
            raise KeyError(f"Device {hostname} not found in collection")
        return self.uuts[hostname]
    
    def __getitem__(self, hostname):
        return self.get_device(hostname)
    
    def __iter__(self):
        return iter(self.uuts.values())
    
    def keys(self):
        return self.uuts.keys()
    
    def values(self):
        return self.uuts.values()
    
    def items(self):
        return self.uuts.items()
    
    def __len__(self):
        return len(self.uuts)
    
    def __contains__(self, hostname):
        return hostname in self.uuts
    
    def __getattr__(self, name):
        """Fanout to all uuts"""
        if not hasattr(UUTWrapper, name):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        def fanout(*args, **kwargs):
            threads = []

            # Pull out optional 'last' hostname; do not forward it to methods
            last = kwargs.pop('last', None)
            
            def wrapper(hostname, uut):
                method = getattr(uut, name)
                return method(*args, **kwargs)
            
            for hostname, uut in self.uuts.items():
                if last and hostname == last:
                    continue
                thread = RThread(target=wrapper, args=(hostname, uut))
                thread.uutname = hostname
                threads.append(thread)
                thread.start()
            
            results = {}
            for thread in threads:
                results[thread.uutname] = thread.join()

            # Execute the 'last' hostname after all others have completed
            if last and last in self.uuts:
                uut = self.uuts[last]
                method = getattr(uut, name)
                results[last] = method(*args, **kwargs)

            return results
        return fanout