import numpy as np
from badger import environment, get_env
from badger.interface import Interface
from operator import itemgetter
import logging


class Environment(environment.Environment):

    name = 'dumb'

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)
        Silly, configs_silly = get_env('silly')
        Naive, configs_naive = get_env('naive')
        self.env_silly = Silly(interface, None)
        self.env_naive = Naive(interface, None)

    def get_var(self, var):
        value = self.env_silly.get_var(var) or self.env_naive.get_var(var)
        if value is None:
            logging.warn(f'Unsupported variable {var}')
        return None

    def set_var(self, var, x):
        if var.startswith('q'):
            self.env_silly.set_var(var, x)
        else:
            self.env_naive.set_var(var, x)

    def get_obs(self, obs):
        if obs == 'l2':
            return self.env_silly.get_obs(obs)
        elif obs == 'mean':
            return self.env_naive.get_obs(obs)
        elif obs == 'l2_x_mean':
            print(self.interface.get_values(['c1', 'c2', 'c3', 'c4', 'c5', 'c6']))
            return self.env_silly.get_obs('l2') * self.env_naive.get_obs('mean')
        else:
            logging.warn(f'Unsupported observation {obs}')
