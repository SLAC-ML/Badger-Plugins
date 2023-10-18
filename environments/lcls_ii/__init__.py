import time
import numpy as np
from badger import environment
from badger.errors import BadgerNoInterfaceError


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
        'EM1K0:GMD:HPS:milliJoulesPerPulse',
        'EM2K0:XGMD:HPS:milliJoulesPerPulse',
        'EM1K0:GMD:HPS:AvgPulseIntensity',
        'EM2K0:XGMD:HPS:AvgPulseIntensity',
    ]

    # Env params
    use_check_var: bool = False  # if check var reaches the target value
    trim_delay: float = 3.0  # in second
    # fault_timeout: float = 5.0  # in second

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

        timeout = 3  # second
        time_start = time.time()
        while np.any(np.array(variable_status.values())):
            time.sleep(0.1 * np.random.rand())

            variable_status = self.interface.get_values(variable_ready_flags)

            time_elapsed = time.time() - time_start
            if time_elapsed > timeout:
                break
