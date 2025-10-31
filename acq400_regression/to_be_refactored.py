
class Waveform:
    """waveform gen functions"""
    def get_zero_crossings(ndarray):
        return np.where(np.diff(np.signbit(ndarray)))[0]
    
    def convert_to_dtype(ndarray, dtype):
        ajust = 0.97 #UUT maxscale is 97% of dtype
        ajust = 1 #ACQ425 ajust
        #return ndarray * 2 ** 15 if dtype == np.int16 else ndarray * 2 ** 31 #old way
        return (ndarray * (np.iinfo(dtype).max * ajust)).astype(dtype)

    def scale_to_dtype(ndarray, dtype):
        return ndarray * np.iinfo(dtype).max
    
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
    
    def get_tolerance(dtype, tolerance=0.035):
        return np.iinfo(dtype).max * tolerance
    
    def get_ideal_wave(
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
        """Returns Ideal wave from args"""
        sense = 1 if rising else -1
        if soft:
            cycles = None
            eindex = 0
            sense = 1
            offset = Waveform.get_wave_start_offset(ndarray, wavelength)
        
        ideal_wave = Waveform.generate_waveform(
            tsamples=tsamples,
            wavelength=wavelength,
            cycles=cycles,
            eindex=eindex,
            translen=translen,
            sense=sense,
            offset=offset,
            waveform=waveform
        )
        #return ideal_wave
        return Waveform.scale_to_dtype(ideal_wave, ndarray.dtype)

    def generate_waveform(
        tsamples,
        wavelength,
        cycles=1,
        eindex=0,
        sense=1,
        translen=None,
        offset=0,
        waveform='SINE',
        scale = [1]
    ):
        """
        Generate a waveform

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
        
        eindex = [eindex] if isinstance(eindex, int) else eindex

        totalwavelength = wavelength * cycles
        translen = translen if translen else totalwavelength

        if waveform.upper() == 'SINE':
            wavearr = np.sin(np.linspace(offset, offset + (cycles * 2) * np.pi, totalwavelength))
            print(wavearr)

        array = np.zeros(tsamples)

        logging.debug("generate_waveform")
        logging.debug(f"tsamples {tsamples}")
        logging.debug(f"eindex {eindex}")
        logging.debug(f"totalwavelength {totalwavelength}")
        logging.debug(f"translen: {translen}")
        logging.debug(f"cycles: {cycles}")
        logging.debug(f"offset: {offset}")
        logging.debug(f"wavelength: {wavelength}")

        for index in eindex:
            if index > tsamples: continue
            translen0 = 0
            translen1 = translen if translen < len(wavearr) else len(wavearr)
            sine = wavearr[translen0: translen1] #extracts portion of sine
            
            extract0 = 0
            extract1 = len(sine)
            
            insert0 = index if sense > 0 else index - (extract1 - extract0) #inserts sine before
            insert1 = index + (extract1 - extract0) if sense > 0 else index #or after the event
            
            trim0 = 0 if insert0 >= 0 else abs(0 - insert0) #calculate trim value for overflow/underflow
            trim1 = 0 if insert1 <= tsamples else abs(tsamples - insert1)

            logging.debug(f"INSERTING WAVEFORM AT INDEX {index}")
            logging.debug(f"SENSE {sense}")
            logging.debug(f"TRIM [{trim0}: {trim1}]")
            logging.debug(f"INSERT [{insert0}: {insert1}]: LEN {(insert1 - insert0)}")
            logging.debug(f"INSERT+TRIM [{insert0 + trim0}: {insert1 - trim1}]: LEN {((insert1 + trim1) - (insert0 - trim0))}")
            logging.debug(f"EXTRACT [{extract0}: {extract1}]: LEN {(extract1 - extract0)}")
            logging.debug(f"EXTRACT+TRIM [{extract0 + trim0}: {extract1 - trim1}]: LEN {((extract1 + trim1) - (extract0 - trim0))}")
        
            array[insert0 + trim0: insert1 - trim1] = sine[extract0 + trim0: extract1 - trim1]
        return array


def check_spad(self, dataset, es_indexes=[]):
        """Checks spad0 is contigious"""
        check = "spad0_contiguous"
        results = []
        log.info(f"Running check {check}")
        for uutname, data in dataset.items():
            result = DotDict()
            if len(data.spad) == 0:
                log.debug(f"{uutname} No Spad")
                continue
            #TODO using a 425 the es doesnt break the spad0 it seems only prepost which
            # removes the sample with the event signature
            diffs = np.diff(data.spad[0])
            mask = self.uuts.generate_es_mask(len(diffs), es_indexes)
            spad0_contiguous = np.all(diffs[mask] == 1)

            results.append(spad0_contiguous)

            result.status = 'passed' if spad0_contiguous else 'failed'
            self.save_data_result(uutname, check, result)

        results = all(results)
        log.debug(f"Check {check} {results}")
        if results:
            log.passed("Spad0 is contiguous")
        else:
            log.failed("Spad0 is non-contiguous")

        return results


def check_wave(self, dataset, ideal_wave):
        """Compares data to an ideal wave"""
        check = "waveforms_valid"
        results = []
        log.info(f"Running check {check}")
        #TODO move this stuff into data handler
        #TODO handle possible different datatypes over uuts and ao,dio only uuts
        for uutname, data in dataset.items():
            result = DotDict()
            failed_chans = []
            dtype = np.int16 if data.format.data_s == 2 else np.int32
            data.tolerance = Waveform.get_tolerance(dtype, self.args.tolerance)

            for chan in self.args.channels:
                waveforms_valid = np.allclose(data.data[chan], ideal_wave[data.es_mask], atol=data.tolerance)
                results.append(waveforms_valid)
                if not waveforms_valid: failed_chans.append(chan)
                
                #TODO feed error indices into the plotting function (sync deviations)
                #diff = np.abs(data.channels[chan] - ideal_wave)
                #out_of_sync_idx = np.where(diff > data.tolerance)[0]
                #print(out_of_sync_idx)

            result.status = 'passed' if len(failed_chans) == 0 else 'failed'
            if len(failed_chans) > 0:
                result.failed_chans = ','.join(map(str, failed_chans))
            self.save_data_result(uutname, check, result)

        results = all(results)
        log.debug(f"Check {check} {results}")

        if results:
            log.passed("Waveforms valid")
        else:
            log.failed("Waveforms not valid")

        return results
    
    
    def get_ideal_wave(self, dataset, soft=False, rising=False):
        """gets the ideal wave using channel data"""

        #TODO clean this up !
        data = self.dataset[self.uuts.master]
        reference = data.channels[self.args.channels[0]]
        tsamples = self.args.get('pre', 0) + self.args.get('post', 0)
        translen = data.translen - data.es_width
        expected_events = self.get_expected_event_signatures(data)
        expected_events += data.es_width

        ideal_wave = Waveform.get_ideal_wave(
            reference, 
            tsamples  = tsamples,
            wavelength = self.args.wavelength,
            cycles = self.args.wave_cycles,
            eindex = expected_events.tolist(),
            translen = translen,
            soft = soft,
            rising = rising,
            waveform ="SINE"
        )
        for uutname, data in dataset.items():
            data.ideal_wave = ideal_wave
        return ideal_wave
    
    def check_es(self, dataset):
        """Check the event signatures are at expected indexes"""
        log.info('Checking event signatures')
        check = "events_correct"
        results = []
        for uutname, data in dataset.items():
            result = DotDict()
            expected = self.get_expected_event_signatures(data)
            events_correct = np.array_equal(data.es_indexes, expected)
            results.append(events_correct)
            result.status = 'passed' if events_correct else 'failed'
            self.save_data_result(uutname, check, result)

            unique_diffs = set(np.diff(data.es_indexes))
            log.debug(f"{uutname} diffs {unique_diffs}")

        results = all(results)

        if results:
            log.passed("Event signatures are at correct indexes")
        else:
            log.failed("Event signatures are at incorrect indexes")
        return results

    def get_expected_event_signatures(self, data):
        """Get expected event signature indexes"""
        if 'translen' not in self.args: return np.array(self.args.get('pre', 0))
        translen = data.translen
        length = self.args.get('pre', 0) + self.args.get('post', 0)
        return np.array(range(0, length, translen))

    def check_passed(self, *args):# if this only checks data rename to check_data
        for uut in self.uuts:
            self.run_state.results[uut].capture.status = 'success'

        plot_data = False
        passed = all(args)
        if passed:
            self.save_run_state('status', 'Passed')
            if self.args.plot == 1: plot_data = True
        else:
            self.save_run_state('status', 'Failed')
            if self.args.plot > 0: plot_data = True

        self.plot_dataset(self.dataset, self.args.channels, plot=plot_data)
        return passed
    
    def catch_error(func):
        """Catches exceptions"""
        print(f'BaseTest.catch_error wrapping {func}')
        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except Exception as e:
                print(f'BaseTest.catch_error caught error in {func}:')
                print(e)
        return wrapper


def plot_dataset(self, dataset, chans=[1], plot=1, save=1):
        """Plot datasets"""
 

        figs = {}
        for uutname, data in dataset.items():
            plot_data = data.format.data_w > 0
            plot_spad = data.format.spad_w > 0
            plot_es = len(data.es_indexes) > 0

            nplot = sum([plot_data, plot_spad, plot_es])
            caxs = 0
            fig, axs = plt.subplots(nplot, 1, figsize=(15, 8), sharex=True)
            axs = [axs] if nplot == 1 else axs

            figs[uutname] = fig
            fig.supxlabel("Samples")
            fig.canvas.manager.set_window_title(f"{uutname}")

            # Fix x axis ticks
            axs[-1].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
            axs[-1].xaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))

            if plot_data:    
                for chan in chans:
                    if self.args.plot_egu:
                        axs[caxs].plot(data.cal_channels(chan), label=f"CH {chan}")
                    else:
                        axs[caxs].plot(data.channels[chan], label=f"CH {chan}")
      
                if hasattr(self, 'ideal_wave3232'): #TODO: use the ideal wave from the dataset
                    ideal_wave = data.ideal_wave
                    tolerance = data.tolerance
                    if self.args.plot_egu:
                        tolerance = self.uuts.chan_to_volts(data.tolerance, *data.calibration[0])
                        ideal_wave = self.uuts.chan_to_volts(data.ideal_wave, *data.calibration[0])

                    #Plot ideal and limits
                    axs[caxs].plot(ideal_wave[data.es_mask] + tolerance, color='#c0392b', linestyle="--", linewidth=1)
                    axs[caxs].plot(ideal_wave[data.es_mask] - tolerance, color='#c0392b', linestyle="--", linewidth=1)
                    axs[caxs].plot(ideal_wave[data.es_mask], color='#27ae60', linestyle="--", linewidth=1, label="Ideal")

                axs[caxs].legend(loc="upper right")
                axs[caxs].set_title('Data')
                if self.args.plot_egu: axs[caxs].set_ylabel("Volts (V)")
                else: axs[caxs].set_ylabel("Codes")
                caxs += 1

            if plot_spad:
                axs[caxs].plot(data.spad[0], label="Spad 0", color='green')
                axs[caxs].set_title('spad 0')
                axs[caxs].set_ylabel("Count")
                caxs += 1

            if plot_es:
                es_arr = np.full(data.chanlen, 0)
                print(f"data.es_width {data.es_width}")
                print(f"len(data.es_indexes) {len(data.es_indexes)}")
                if data.es_width == 0:
                    es_ajust = np.zeros(len(data.es_indexes),  dtype=int)
                else:
                    es_ajust = np.arange(0, len(data.es_indexes) * data.es_width, data.es_width,  dtype=int)

                #es_ajust = np.arange(0, len(data.es_indexes) * data.es_width, data.es_width)

                print(f"es_ajust {es_ajust}")
                print(f"data.es_indexes {data.es_indexes}")
                es_arr[data.es_indexes - es_ajust] = 1
                axs[caxs].plot(es_arr, color='blue', label="Event Signatures")
                axs[caxs].set_yticks([0, 1], labels=["0", "1"])
                axs[caxs].set_title('Event Signatures')
                caxs += 1

            fig.tight_layout()

            if save:
                filename = f"{uutname}.png"
                log.debug(f"saving {uutname} plot to {filename}")
                fig.savefig(filename)

        if plot:
            log.info("Plotting Datasets")
            plt.show()
        plt.close()