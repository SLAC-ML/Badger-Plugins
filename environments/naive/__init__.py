import numpy as np
from badger import environment
from badger.interface import Interface


class Environment(environment.Environment):

    name = 'naive'
    var_channel_map = {
        's1': 'c5',
        's2': 'c6',
    }

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

    @staticmethod
    def list_vars():
        return ['s1', 's2']

    @staticmethod
    def list_obses():
        return ['max', 'min', 'mean']

    @staticmethod
    def get_default_params():
        return None

    def _get_var(self, var):
        return self.interface.get_value(self.var_channel_map[var])

    def _set_var(self, var, x):
        self.interface.set_value(self.var_channel_map[var], x)

    def _get_obs(self, obs):
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
