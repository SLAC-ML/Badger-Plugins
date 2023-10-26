import logging
import time
import numpy as np
from edef import EventDefinition
from badger import environment
from badger.errors import BadgerNoInterfaceError, BadgerEnvObsError


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
    }
    observables = [
        'sxr_pulse_intensity',
    ]

    # Env params
    method: int = 1
    # For method 0
    xgmd: bool = False
    avg: bool = False
    # For method 1
    event_code: str = 'SCS'  # could also be '31', '32'
    custom_acq_rate: float = 100  # for custom event code
    points: int = 100
    loss_pv: str = 'LBLM:COL0:862:A:I0_LOSSSCSHH'  # loss monitor PV
    stats: str = 'percent_80'
    # Var setters
    use_check_var: bool = False  # if check var reaches the target value
    check_var_timeout: float = 3.0  # tumeout for the var check
    trim_delay: float = 7.0  # in second
    # MPS fault check
    check_fault_timeout: float = 5.0  # in second

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

    def get_sxr_pulse_intensity(self):
        # self.method
        # 0: scalar
        # 1: BSA buffer
        # 2: manually data collection
        if self.method == 0:
            if self.xgmd:
                if self.avg:
                    value = self.interface.get_value(
                        'EM2K0:XGMD:HPS:AvgPulseIntensity')
                else:
                    value = self.interface.get_value(
                        'EM2K0:XGMD:HPS:milliJoulesPerPulse')
            else:
                if self.avg:
                    value = self.interface.get_value(
                        'EM1K0:GMD:HPS:AvgPulseIntensity')
                else:
                    value = self.interface.get_value(
                        'EM1K0:GMD:HPS:milliJoulesPerPulse')

            return value
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
                    rate = 10
                else:
                    PV_gas = 'EM1K0:GMD:HPS:milliJoulesPerPulseHSTSCSHH'
                    rate = 100
            else:
                PV_gas = f'EM1K0:GMD:HPS:milliJoulesPerPulseHST{self.event_code}'
                rate = self.custom_acq_rate
            logging.info(f'SXR dump acquisition rate: {rate} Hz')

            # Wait enough time to accumulate sufficient data points in buffers
            nap_time = points / rate
            time.sleep(nap_time)

            data_raw = self.interface.get_value(PV_gas)
            data = data_raw[-points:]
            obj_tar = np.percentile(data, 80)
            obj_mean = np.mean(data)
            obj_median = np.median(data)
            obj_std = np.std(data)

            stats_dict = {
                'percent_80': obj_tar,
                'mean': obj_mean,
                'median': obj_median,
                'std': obj_std,
            }

            return stats_dict[self.stats]
        elif self.method == 2:
            raise NotImplementedError()
        else:
            raise NotImplementedError()

    def check_fault_status(self):
        ts_start = time.time()
        while True:
            req_rate = self.interface.get_value('TPG:SYS0:1:DST04:REQRATE')
            act_rate = self.interface.get_value('TPG:SYS0:1:DST04:RATE')
            is_rate_matched = (req_rate == act_rate)

            permit_MPS = self.interface.get_value(
                'SIOC:SYS0:MP00:SC_SXR_BC', as_string=True)
            is_beam_on = (permit_MPS != 'Beam Off')

            if is_rate_matched and is_beam_on:
                break
            else:
                ts_curr = time.time()
                dt = ts_curr - ts_start
                if dt > self.check_fault_timeout:
                    raise BadgerEnvObsError

                time.sleep(0.1 * np.random.rand())

    def get_observables(self, observable_names: list[str]) -> dict:
        if self.interface is None:
            raise BadgerNoInterfaceError

        # Make sure machine is not in a fault state
        self.check_fault_status()

        observable_outputs = {}
        for obs in observable_names:
            if obs == 'sxr_pulse_intensity':
                value = self.get_sxr_pulse_intensity()

            observable_outputs[obs] = value

        return observable_outputs
