import time
import numpy as np
from operator import itemgetter
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

    def get_value(self, channel: str):
        try:
            pv = self.pvs[channel]
        except KeyError:
            pv = epics.get_pv(channel)
            self.pvs[channel] = pv

        if not pv.wait_for_connection(1):
            # TODO: consider throwing an exception here
            return None

        while True:
            value = pv.get()
            if value is not None:
                break

            time.sleep(0.1)

        return value

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
