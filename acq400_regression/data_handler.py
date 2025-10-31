
"""
dataset class 
- read raw bianry data from socket
- get data specification
- reform bianry data into data channels

Usage 

from ac400_regression.data_handler import Dataset

dataset = Dataset(self.controller.uuts)
dataset.read_data()
#dataset.gen_expected_wave(soft, rising)
dataset.check_sync()
dataset.check_es()
dataset.check_spad()
dataset.free_memory()
dataset.save_to_disk()
dataset.plot_data()
dataset.save_plot()


"""

from pprint import pprint
import numpy as np
import logging
from acq400_regression.utilities import DotDict

class Dataset():
    def __init__(self, uuts, transient=True):
        logging.debug(f"Dataset Init {uuts.hostnames} transient {transient}")
        self.uuts = uuts
        self.init_uuts(uuts, transient)

    def __getitem__(self, key):
        return self._data[key]
    
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()
        
    def init_uuts(self, uuts, transient):
        self.uuts = uuts
        self._data = {}
        mask = None
        for uutname, uut in self.uuts.items():
            if not transient: mask = uut.get_stream_mask()
            self._data[uutname] = DotDict()
            self._data[uutname].format = uut.get_sample_format(mask)

    def import_data(self):
        for uut in self.uuts.values():
            data = DotDict()
            data.format = uut.get_sample_format()
            data.raw = np.array(uut.read_channels(0)[0], copy=True)
            data.samples = data.raw.view(dtype=data.format.dtype).reshape(-1)
            data.datalen = len(data.samples)
            data.es_indexes = self.find_event_signatures(data.raw, data.format.sample_bytes, data.format.data_size)
            data.es_mask = self.generate_es_mask(data.datalen, data.es_indexes)

            data.channels = {int(chan): data.samples[chan][data.es_mask] for chan in data.samples.dtype.names}
            logging.debug(f"{uut.hostname} transient import {data['raw'].nbytes} Bytes")
            self._data[uut.hostname] = data

    def find_event_signatures(self, data, sample_bytes, data_size):
        """Finds event signatures in data"""
        logging.debug('Finding event signatures')

        channels = sample_bytes // 4
        trim = None
        if data_size == 2:
            trim = sample_bytes % 4
            if trim == 0: trim = None
        data32 = data[:trim].view(dtype=np.uint32).reshape(-1, channels).T

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

    def generate_es_mask(self, datalen, es_indexes):
        """Generates a mask to exclude the event signatures"""
        es_mask = np.full(datalen, True)
        if len(es_indexes) > 0: es_mask[es_indexes] = False
        return es_mask

    def get_tolerance(self, dtype, tolerance=0.035):
        return np.iinfo(dtype).max * tolerance



class DataChecks:
    def __init__(self, dataset):
        pass

    def check_spad0(self): pass

    def check_es_indices(self): pass

    def check_waveform_coherence(self, tolerence): pass




class DataPlotter:
    @staticmethod
    def plot():
        pass
    
    @staticmethod
    def save_to_file():
        pass
