import numpy as np
from badger import environment, get_env
from badger.interface import Interface
from operator import itemgetter
import logging


class Environment(environment.Environment):

    name = 'silly'
    var_channel_map = {
        'q1': 'c1',
        'q2': 'c2',
        'q3': 'c3',
        'q4': 'c4',
    }

    def __init__(self, interface: Interface, params):
        # ENV, configs = get_env('TNK')
        # env = ENV(interface, configs['params'])
        # print(env)
        super().__init__(interface, params)

    def get_var(self, var):
        return self.interface.get_value(self.var_channel_map[var])

    def set_var(self, var, x):
        self.interface.set_value(self.var_channel_map[var], x)

    def get_obs(self, obs):
        if obs == 'l1':
            values = self.interface.get_values(
                ['c1', 'c2', 'c3', 'c4'])
            return np.sum(np.abs(values))
        elif obs == 'l2':
            return self.interface.get_value('norm')
        elif obs == 'min':
            values = self.interface.get_values(
                ['c1', 'c2', 'c3', 'c4'])
            return np.min(values)
        elif obs == 'max':
            values = self.interface.get_values(
                ['c1', 'c2', 'c3', 'c4'])
            return np.max(values)
        elif obs == 'mean':
            values = self.interface.get_values(
                ['c1', 'c2', 'c3', 'c4'])
            return np.mean(values)
        else:
            logging.warn(f'Unsupported observation {obs}')
