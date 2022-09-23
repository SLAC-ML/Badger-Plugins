import time
import numpy as np
import epics
from badger import interface

epics.ca.DEFAULT_CONNECTION_TIMEOUT = 0.1


class Interface(interface.Interface):

    name = 'epics'

    def __init__(self, params=None):
        super().__init__(params)

        self.pvs = {}  # epics pvs (not values!)

    @staticmethod
    def get_default_params():
        return None

    @interface.log
    def get_value(self, channel: str, as_string=False):
        try:
            pv = self.pvs[channel]
        except KeyError:
            pv = epics.get_pv(channel)
            self.pvs[channel] = pv

        if not pv.wait_for_connection(1):
            # TODO: consider throwing an exception here
            return None

        count_down = 2  # second
        while count_down > 0:
            value = pv.get(as_string=as_string)
            try:
                _ = len(value)
                value = value[~np.isnan(value)]
                if len(value):
                    return value
            except:
                if (value is not None) and (not np.isnan(value)):
                    return value

            time.sleep(0.1)
            count_down -= 0.1

        raise Exception(f'PV {channel} readout ({value}) is invalid!')

    @interface.log
    def set_value(self, channel: str, value):
        try:
            pv = self.pvs[channel]
        except KeyError:
            pv = epics.get_pv(channel)
            self.pvs[channel] = pv

        if not pv.wait_for_connection(1):
            # TODO: consider throwing an exception here
            return None

        # Wait for no longer 5s
        pv.put(value, wait=True, timeout=3)
        # The following might not make sense
        # since usually we should set one channel but monitor
        # a corresponding but different channel
        count_down = 2  # second
        while count_down > 0:
            _value = pv.get()
            if value:
                if np.isclose(_value, value, rtol=1e-3):
                    return _value
            else:
                if np.isclose(_value, value, atol=1e-3):
                    return _value

            time.sleep(0.1)
            count_down -= 0.1

        raise Exception(f'PV {channel} (current: {_value}) cannot reach expected value ({value})!')
