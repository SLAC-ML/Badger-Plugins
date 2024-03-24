import logging
import time
import numpy as np
from badger import environment
from badger.errors import BadgerNoInterfaceError, BadgerEnvObsError
from .utils import get_buffer_stats


class Environment(environment.Environment):

    name = 'lcls_ii'
    variables = {
        'QUAD:COL1:120:BCTRL': [],
        'QUAD:COL1:260:BCTRL': [],
        'QUAD:COL1:280:BCTRL': [],
        'QUAD:COL1:320:BCTRL': [],
        'QUAD:EMIT2:150:BCTRL': [],
        'QUAD:EMIT2:300:BCTRL': [],
        'QUAD:EMIT2:800:BCTRL': [],
        'QUAD:EMIT2:900:BCTRL': [],
        'QUAD:DOG:250:BCTRL': [],
        'QUAD:DOG:280:BCTRL': [],
        'QUAD:DOG:335:BCTRL': [],
        'QUAD:DOG:405:BCTRL': [],
        'QUAD:LTUS:620:BCTRL': [],
        'QUAD:LTUS:640:BCTRL': [],
        'QUAD:LTUS:660:BCTRL': [],
        'QUAD:LTUS:680:BCTRL': [],
        'QUAD:HTR:120:BCTRL': [],
    }
    observables = [
        'sxr_pulse_intensity_p80',
        'sxr_pulse_intensity_mean',
        'sxr_pulse_intensity_median',
        'sxr_pulse_intensity_std',
        'beam_loss',
        'beamsize_x',
        'beamsize_y',
        'beamsize_r',
        'beamsize_g',
    ]

    # Env params
    method: int = 1
    # For method 0
    xgmd: bool = False
    avg: bool = False
    loss_pv: str = 'LBLM:COL0:862:A:I0_LOSS'  # loss monitor PV prefix
    # For method 1
    event_code: str = 'SCS'  # could also be '31', '32'
    custom_acq_rate: float = 100  # for custom event code
    points: int = 100
    stats: str = 'percent_80'
    # Var setters
    use_check_var: bool = False  # if check var reaches the target value
    check_var_timeout: float = 3.0  # tumeout for the var check
    trim_delay: float = 7.0  # in second
    # MPS fault check
    check_fault_timeout: float = 5.0  # in second
    lasering: bool = True  # if it's lasering

    def get_bounds(self, variable_names):
        if self.interface is None:
            raise BadgerNoInterfaceError

        pvs_low = [v + '.DRVL' for v in variable_names]
        pvs_high = [v + '.DRVH' for v in variable_names]
        bounds_low = self.interface.get_values(pvs_low)
        bounds_high = self.interface.get_values(pvs_high)

        bound_outputs = {}
        for i, v in enumerate(variable_names):
            bound_outputs[v] = [
                bounds_low[pvs_low[i]],
                bounds_high[pvs_high[i]]]

        return bound_outputs

    def get_variables(self, variable_names: list[str]) -> dict:
        if self.interface is None:
            raise BadgerNoInterfaceError

        channel_names = []
        for v in variable_names:
            if v.endswith(':BCTRL'):
                prefix = v[:v.rfind(':')]
                readback = prefix + ':BACT'
            else:
                readback = v
            channel_names.append(readback)
        channel_outputs = self.interface.get_values(channel_names)

        variable_outputs = {v: channel_outputs[channel_names[i]]
                            for i, v in enumerate(variable_names)}

        return variable_outputs

    def set_variables(self, variable_inputs: dict[str, float]):
        if self.interface is None:
            raise BadgerNoInterfaceError

        self.interface.set_values(variable_inputs)

        if not self.use_check_var:
            if self.trim_delay:
                time.sleep(self.trim_delay)  # extra time for stablizing orbits

            return

        variable_ready_flags = [v[:v.rfind(':')] + ':STATCTRLSUB.T'
                                for v in variable_inputs
                                if v.endswith(':BCTRL')]
        variable_status = self.interface.get_values(variable_ready_flags)

        time_start = time.time()
        while np.any(np.array(variable_status.values())):
            time.sleep(0.1 * np.random.rand())

            variable_status = self.interface.get_values(variable_ready_flags)

            time_elapsed = time.time() - time_start
            if time_elapsed > self.check_var_timeout:
                break

        if self.trim_delay:
            time.sleep(self.trim_delay)  # extra time for stablizing orbits

    def get_intensity_n_loss(self):
        # self.method
        # 0: scalar
        # 1: BSA buffer
        # 2: manually data collection
        if self.method == 0:
            if self.xgmd:
                if self.avg:
                    intensity = self.interface.get_value(
                        'EM2K0:XGMD:HPS:AvgPulseIntensity')
                else:
                    intensity = self.interface.get_value(
                        'EM2K0:XGMD:HPS:milliJoulesPerPulse')
            else:
                if self.avg:
                    intensity = self.interface.get_value(
                        'EM1K0:GMD:HPS:AvgPulseIntensity')
                else:
                    intensity = self.interface.get_value(
                        'EM1K0:GMD:HPS:milliJoulesPerPulse')

            loss = self.interface.get_value(self.loss_pv)

            return intensity, intensity, intensity, 0, loss
        elif self.method == 1:
            points = self.points
            logging.info(f'Get value of {points} points')

            req_rate = self.interface.get_value('TPG:SYS0:1:DST04:REQRATE')

            if not req_rate:
                raise BadgerEnvObsError

            req_rate = float(req_rate)
            if self.event_code == 'SCS':
                if req_rate < 100:
                    PV_gas = 'EM1K0:GMD:HPS:milliJoulesPerPulseHSTSCSTH'
                    PV_loss = f'{self.loss_pv}HSTSCSTH'
                    rate = 10
                else:
                    PV_gas = 'EM1K0:GMD:HPS:milliJoulesPerPulseHSTSCSHH'
                    PV_loss = f'{self.loss_pv}HSTSCSHH'
                    rate = 100
            else:
                PV_gas = f'EM1K0:GMD:HPS:milliJoulesPerPulseHST{self.event_code}'
                PV_loss = f'{self.loss_pv}HST{self.event_code}'
                rate = self.custom_acq_rate
            logging.info(f'Data acquisition rate: {rate} Hz')

            # Wait enough time to accumulate sufficient data points in buffers
            nap_time = points / rate
            time.sleep(nap_time)

            # Filter out the NaNs
            results_dict = self.interface.get_values([PV_gas, PV_loss])
            intensity_raw = results_dict[PV_gas][-points:]
            loss_raw = results_dict[PV_loss][-points:]
            ind_valid = ~np.logical_or(np.isnan(intensity_raw), np.isnan(loss_raw))
            intensity_valid = intensity_raw[ind_valid]
            loss_valid = intensity_raw[ind_valid]

            n_valid = len(intensity_valid)
            if not n_valid:
                raise BadgerEnvObsError("All points in buffer are NaNs!")

            logging.info(f'Valid point number in buffer: {n_valid}')

            stats_intensity = get_buffer_stats(intensity_valid)
            stats_loss = get_buffer_stats(loss_valid)

            return stats_intensity['percent_80'], \
                stats_intensity['mean'], \
                stats_intensity['median'], \
                stats_intensity['std'], \
                stats_loss[self.stats]
        elif self.method == 2:
            raise NotImplementedError
        else:
            raise NotImplementedError

    def check_fault_status(self):
        if self.lasering:
            MPS_PV = 'SIOC:SYS0:MP00:SC_SXR_BC'
        else:
            MPS_PV = 'SIOC:SYS0:MP00:SC_BSYD_BC'

        ts_start = time.time()
        while True:
            # req_rate = self.interface.get_value('TPG:SYS0:1:DST04:REQRATE')
            # act_rate = self.interface.get_value('TPG:SYS0:1:DST04:RATE')
            # is_rate_matched = (req_rate == act_rate)

            permit_MPS = self.interface.get_value(
                MPS_PV, as_string=True)
            is_beam_on = (permit_MPS != 'Beam Off')

            # if is_rate_matched and is_beam_on:
            if is_beam_on:
                break
            else:
                ts_curr = time.time()
                dt = ts_curr - ts_start
                if dt > self.check_fault_timeout:
                    raise BadgerEnvObsError

                time.sleep(0.1 * np.random.rand())

    def is_sxr_pulse_intensity_observed(self, observable_names):
        return len([name for name in observable_names if
                    name.startswith('sxr_pulse_intensity')])

    def is_beam_loss_observed(self, observable_names):
        return 'beam_loss' in observable_names

    def get_observables(self, observable_names: list[str]) -> dict:
        if self.interface is None:
            raise BadgerNoInterfaceError

        # Make sure machine is not in a fault state
        self.check_fault_status()

        if self.is_sxr_pulse_intensity_observed(observable_names) or \
           self.is_beam_loss_observed(observable_names):
            intensity_p80, intensity_mean, intensity_median, intensity_std, \
                loss = self.get_intensity_n_loss()

        observable_outputs = {}
        for obs in observable_names:
            if obs == 'sxr_pulse_intensity_p80':
                value = intensity_p80
            elif obs == 'sxr_pulse_intensity_mean':
                value = intensity_mean
            elif obs == 'sxr_pulse_intensity_median':
                value = intensity_median
            elif obs == 'sxr_pulse_intensity_std':
                value = intensity_std
            elif obs == 'beam_loss':
                value = loss
            elif obs == 'beamsize_x':
                value = self.interface.get_value('OTRS:HTR:330:XRMS')
            elif obs == 'beamsize_y':
                value = self.interface.get_value('OTRS:HTR:330:YRMS')
            elif obs == 'beamsize_r':
                bs_x = self.interface.get_value('OTRS:HTR:330:XRMS')
                bs_y = self.interface.get_value('OTRS:HTR:330:YRMS')
                value = np.linalg.norm([bs_x, bs_y])
            elif obs == 'beamsize_g':
                bs_x = self.interface.get_value('OTRS:HTR:330:XRMS')
                bs_y = self.interface.get_value('OTRS:HTR:330:YRMS')
                value = np.sqrt(bs_x * bs_y)
            else:
                raise NotImplementedError

            observable_outputs[obs] = value

        return observable_outputs
