import numpy as np
from badger import interface
from operator import itemgetter
import logging
import epics

epics.ca.DEFAULT_CONNECTION_TIMEOUT = 0.1


class Interface(interface.Interface):

    name = 'epics'

    def __init__(self, params):
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

        if not pv.connected:
            pv.connect()
            # TODO: consider throwing an exception here

        while True:
            value = pv.get()
            if value is not None:
                break

        return value

    def set_value(self, channel: str, value):
        try:
            pv = self.pvs[channel]
        except KeyError:
            pv = epics.get_pv(channel)
            self.pvs[channel] = pv

        if not pv.connected:
            # TODO: consider throwing an exception here
            return None
        else:
            return pv.put(value)
