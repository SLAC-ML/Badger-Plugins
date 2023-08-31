import random
import time
import numpy as np
from typing import Dict
import epics
from badger import interface

epics.ca.DEFAULT_CONNECTION_TIMEOUT = 0.1


class Interface(interface.Interface):

    name = 'epics'
    testing: bool = False

    # Private variables
    _pvs: Dict = {}

    @interface.log
    def get_values(self, channel_names, as_string: bool = False):
        channel_outputs = {}

        # if testing generate some random numbers and return before starting epics
        if self.testing:
            for channel in channel_names:
                channel_outputs[channel] = random.random()

            return channel_outputs

        for channel in channel_names:
            try:
                pv = self._pvs[channel]
            except KeyError:
                pv = epics.get_pv(channel)
                self._pvs[channel] = pv

            if not pv.wait_for_connection(1):
                # TODO: consider throwing an exception here
                channel_outputs[channel] = None
                continue

            count_down = 2  # second
            flag = True
            while count_down > 0:
                value = pv.get(as_string=as_string)
                try:
                    _ = len(value)
                    value = value[~np.isnan(value)]
                    if len(value):
                        channel_outputs[channel] = value
                        flag = False
                        break
                except:
                    if (value is not None) and (not np.isnan(value)):
                        channel_outputs[channel] = value
                        flag = False
                        break

                time.sleep(0.1)
                count_down -= 0.1

            if flag:
                raise Exception(f'PV {channel} readout ({channel_outputs[channel]}) is invalid!')

        return channel_outputs

    @interface.log
    def set_values(self, channel_inputs: Dict) -> Dict:
        channel_outputs = {}

        if self.testing:
            for channel in channel_inputs.keys():
                channel_outputs[channel] = 1.0

            return channel_outputs

        for channel, value in channel_inputs.items():
            try:
                pv = self._pvs[channel]
            except KeyError:
                pv = epics.get_pv(channel)
                self._pvs[channel] = pv

            if not pv.wait_for_connection(1):
                # TODO: consider throwing an exception here
                channel_outputs[channel] = None
                continue

            # Wait for no longer 5s
            pv.put(value, wait=True, timeout=3)
            # The following might not make sense
            # since usually we should set one channel but monitor
            # a corresponding but different channel
            count_down = 2  # second
            flag = True
            while count_down > 0:
                _value = pv.get()
                if value:
                    if np.isclose(_value, value, rtol=1e-3):
                        channel_outputs[channel] = _value
                        flag = False
                        break
                else:
                    if np.isclose(_value, value, atol=1e-3):
                        channel_outputs[channel] = _value
                        flag = False
                        break

                time.sleep(0.1)
                count_down -= 0.1

            if flag:
                raise Exception(f'PV {channel} (current: {channel_outputs[channel]}) cannot reach expected value ({value})!')

        return channel_outputs
