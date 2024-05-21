#!/usr/bin/env python3
import numpy as np
from acq400_regression.misc import tri

from acq400_hapi import PR, pprint, pv #remove me after testing

class Waveform:
    def get_zero_crossings(ndarray):
        return np.where(np.diff(np.signbit(ndarray)))[0]
    
    def scale_to_max_dtype(ndarray, dtype=np.int16):
        return ndarray * 2 ** 15 if dtype == np.int16 else ndarray * 2 ** 31
    
    def scale_to_target(ndarray, target):
        target = target - np.mean(target)
        return ndarray * ((np.amax(target) - np.amin(target)) / 2)
    
    def get_wave_start_offset(ndarray, wavelength):
        zero_crossings = Waveform.get_zero_crossings(ndarray)
        if 0 >= len(zero_crossings): return 0
        first_zc = zero_crossings[0]
        value = 40
        crossing_pos = 0 if (ndarray[first_zc-value] < 0 and ndarray[first_zc+value] > 0) else np.pi #40?
        return crossing_pos - ((first_zc)/wavelength) * 2 *np.pi
    
    def get_tolerance(wave, tolerance=0.025):
        return np.iinfo(wave.dtype).max * tolerance
    
    def generate_ideal_wave(
        ndarray,
        tsamples,
        wavelength,
        cycles=1,
        eindex=0,
        translen=None,
        offset=0, 
        soft=False, 
        rising=True,
        waveform='SINE'
        ):
        PR.Purple("[generate_ideal_wave]")
        """Returns Ideal wave from args"""
        sense = 1 if rising else -1
        print(f"if soft {soft}")
        if soft:
            cycles = None
            eindex = 0
            sense = 1
            offset = Waveform.get_wave_start_offset(ndarray, wavelength)
        
        """ideal_wave = Waveform.generate_sine(
            tsamples=tsamples,
            wavelength=wavelength,
            cycles=cycles,
            eindex=eindex,
            translen=translen,
            sense=sense,
            offset=offset,
        )"""
        ideal_wave = Waveform.generate_sine2(
            tsamples=tsamples,
            wavelength=wavelength,
            cycles=cycles,
            eindex=eindex,
            translen=translen,
            sense=sense,
            offset=offset,
            waveform=waveform
        )
        return Waveform.scale_to_max_dtype(ideal_wave, ndarray.dtype)
        
    def generate_sine(
        tsamples,
        wavelength,
        cycles=1,
        events=0,
        sense=1,
        translen=None,
        offset=0,
    ):
        """
            Generate a sine waveform
        
        Args:
            tsamples (int): total samples
            wavelength (int): sine wavelength in samples
            cycles (float, optional): number of cycles of sine. Defaults to 1.
            event (int, optional): indexes to insert sine. Defaults to 0.
            sense (int, optional): 1: Rising -1: Falling. Defaults to 1.
            translen (int, optional): length of sine to insert. Defaults to None.
            offset (float, optional): sine start offset. Defaults to 0.
        """

        cycles = cycles if cycles else int(tsamples / wavelength)
        
        events = events if isinstance(events, list) else [events] #converts single int to list

        totalwavelength = wavelength * cycles
        translen = translen if translen else totalwavelength

        sine_arr = np.sin(np.linspace(offset, offset + (cycles * 2) * np.pi, totalwavelength))
        array = np.zeros(tsamples)

        """print()
        print('GENERATE SINE')
        print(f"events {events}")
        print(f"totalwavelength {totalwavelength}")
        print(f"translen: {translen}")
        print(f"cycles: {cycles}")
        print(f"offset: {offset}")
        print(f"wavelength: {wavelength}")"""

        for event in events:
            translen0 = 0
            translen1 = translen if translen < len(sine_arr) else len(sine_arr)
            sine = sine_arr[translen0: translen1] #extracts portion of sine
            
            extract0 = 0
            extract1 = len(sine)
            
            insert0 = event if sense > 0 else event - (extract1 - extract0) #inserts sine before
            insert1 = event + (extract1 - extract0) if sense > 0 else event #or after the event"""
            
            trim0 = 0 if insert0 >= 0 else abs(0 - insert0) #calculate trim value for overflow/underflow
            trim1 = 0 if insert1 <= tsamples else abs(tsamples - insert1)
            
            """print()
            print(f"INSERTING EVENT AT INDEX {event}")
            print(f"SENSE {sense}")
            print(f"TRIM [{trim0}: {trim1}]")
            print(f"INSERT [{insert0}: {insert1}]: LEN {(insert1 - insert0)}")
            print(f"INSERT+TRIM [{insert0 + trim0}: {insert1 - trim1}]: LEN {((insert1 + trim1) - (insert0 - trim0))}")
            print(f"EXTRACT [{extract0}: {extract1}]: LEN {(extract1 - extract0)}")
            print(f"EXTRACT+TRIM [{extract0 + trim0}: {extract1 - trim1}]: LEN {((extract1 + trim1) - (extract0 - trim0))}")"""
            
            array[insert0 + trim0: insert1 - trim1] = sine[extract0 + trim0: extract1 - trim1]
            
        return array

    def generate_sine2(
        tsamples,
        wavelength,
        waveform='SINE',
        cycles=1,
        eindex=0,
        sense=1,
        translen=None,
        offset=0,
    ):
        """
            Generate a square waveform TODO
        
        Args:
            tsamples (int): total samples
            wavelength (int): sine wavelength in samples
            cycles (float, optional): number of cycles of sine. Defaults to 1.
            eindex (int, optional): indexes of to insert sine. Defaults to 0.
            sense (int, optional): 1: Rising -1: Falling. Defaults to 1.
            translen (int, optional): length of sine to insert. Defaults to None.
            offset (float, optional): sine start offset. Defaults to 0.
        """

        cycles = cycles if cycles else int(tsamples / wavelength)
        
        eindex = eindex if isinstance(eindex, list) else [eindex] #converts single int to list

        totalwavelength = wavelength * cycles
        translen = translen if translen else totalwavelength


        if waveform.upper() == 'SINE':
            wavearr = np.sin(np.linspace(offset, offset + (cycles * 2) * np.pi, totalwavelength))
        if waveform.upper() == 'SQUARE':
            PR.Red(f"totalwavelength {totalwavelength}")
            wavearr = np.zeros(totalwavelength)
            wavearr[:int(totalwavelength / 2)] += 1
            wavearr[int(totalwavelength / 2):] -= 1
            print(len(wavearr[:int(totalwavelength / 2)]))
            print(len(wavearr[int(totalwavelength / 2):]))
        
        
        
        
        array = np.zeros(tsamples)

        """print()
        print('GENERATE SINE')
        print(f"eindex {eindex}")
        print(f"totalwavelength {totalwavelength}")
        print(f"translen: {translen}")
        print(f"cycles: {cycles}")
        print(f"offset: {offset}")
        print(f"wavelength: {wavelength}")"""

        for index in eindex:
            translen0 = 0
            translen1 = translen if translen < len(wavearr) else len(wavearr)
            sine = wavearr[translen0: translen1] #extracts portion of sine
            
            extract0 = 0
            extract1 = len(sine)
            
            insert0 = index if sense > 0 else index - (extract1 - extract0) #inserts sine before
            insert1 = index + (extract1 - extract0) if sense > 0 else index #or after the event"""
            
            trim0 = 0 if insert0 >= 0 else abs(0 - insert0) #calculate trim value for overflow/underflow
            trim1 = 0 if insert1 <= tsamples else abs(tsamples - insert1)
            
            """print()
            print(f"INSERTING WAVEFORM AT INDEX {index}")
            print(f"SENSE {sense}")
            print(f"TRIM [{trim0}: {trim1}]")
            print(f"INSERT [{insert0}: {insert1}]: LEN {(insert1 - insert0)}")
            print(f"INSERT+TRIM [{insert0 + trim0}: {insert1 - trim1}]: LEN {((insert1 + trim1) - (insert0 - trim0))}")
            print(f"EXTRACT [{extract0}: {extract1}]: LEN {(extract1 - extract0)}")
            print(f"EXTRACT+TRIM [{extract0 + trim0}: {extract1 - trim1}]: LEN {((extract1 + trim1) - (extract0 - trim0))}")"""
            
            array[insert0 + trim0: insert1 - trim1] = sine[extract0 + trim0: extract1 - trim1]
            
        return array

    