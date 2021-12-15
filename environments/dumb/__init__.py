import numpy as np
from badger import environment
from badger.factory import get_env
from badger.interface import Interface
from operator import itemgetter
import logging


class Environment(environment.Environment):

    name = 'dumb'

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)
        Silly, configs_silly = get_env('silly')
        Naive, configs_naive = get_env('naive')
        self.env_silly = Silly(interface, configs_silly['params'])
        self.env_naive = Naive(interface, configs_naive['params'])

    @staticmethod
    def list_vars():
        return ['q1', 'q2', 'q3', 'q4', 's1', 's2']

    @staticmethod
    def list_obses():
        return ['l2', 'mean', 'l2_x_mean']

    @staticmethod
    def get_default_params():
        return None

    def _get_var(self, var):
        try:
            return self.env_silly._get_var(var)
        except Exception:
            pass

        try:
            return self.env_naive._get_var(var)
        except Exception:
            pass

        raise Exception(f'Invalid variable {var}')

    def _set_var(self, var, x):
        if var.startswith('q'):
            self.env_silly.set_var(var, x)
        else:
            self.env_naive.set_var(var, x)

    def _get_obs(self, obs):
        if obs == 'l2':
            return self.env_silly.get_obs(obs)
        elif obs == 'mean':
            return self.env_naive.get_obs(obs)
        elif obs == 'l2_x_mean':
            return self.env_silly.get_obs('l2') * self.env_naive.get_obs('mean')
