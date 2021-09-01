import numpy as np
from badger import environment
from badger.interface import Interface
from operator import itemgetter
import logging


class Environment(environment.Environment):

    name = 'naive'
    var_channel_map = {
        's1': 'c5',
        's2': 'c6',
    }

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

    def get_var(self, var):
        return self.interface.get_value(self.var_channel_map[var])

    def set_var(self, var, x):
        self.interface.set_value(self.var_channel_map[var], x)

    def get_obs(self, obs):
        if obs == 'min':
            values = self.interface.get_values(
                ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'])
            return np.min(values)
        elif obs == 'max':
            values = self.interface.get_values(
                ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'])
            return np.max(values)
        elif obs == 'mean':
            values = self.interface.get_values(
                ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'])
            return np.mean(values)
        else:
            logging.warn(f'Unsupported observation {obs}')
