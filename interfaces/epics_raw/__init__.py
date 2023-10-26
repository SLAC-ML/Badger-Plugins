import random
import epics
from badger import interface

epics.ca.DEFAULT_CONNECTION_TIMEOUT = 0.1


class Interface(interface.Interface):
    name = "epics_raw"

    testing: bool = False
    timeout: float = None

    @interface.log
    def get_values(self, channel_names, as_string: bool = False):
        channel_outputs = {}

        # if testing generate some random numbers and return
        # before starting epics
        if self.testing:
            for channel in channel_names:
                channel_outputs[channel] = random.random()

            return channel_outputs

        values = epics.caget_many(channel_names, as_string=as_string,
                                  timeout=self.timeout)
        for i, channel in enumerate(channel_names):
            channel_outputs[channel] = values[i]

        return channel_outputs

    @interface.log
    def set_values(self, channel_inputs: dict) -> dict:
        channel_flags = {}

        pvlist = list(channel_inputs.keys())
        values = list(channel_inputs.values())

        if self.testing:
            for channel in pvlist:
                channel_flags[channel] = 1

            return channel_flags

        flags = epics.caput_many(pvlist, values, wait="all")

        for i, channel in enumerate(pvlist):
            channel_flags[channel] = flags[i]

        return channel_flags
