import time
import numpy as np
from badger import environment
from badger.interface import Interface


class Environment(environment.Environment):

    name = 'silly_slow'
    var_channel_map = {
        'q1': 'c1',
        'q2': 'c2',
        'q3': 'c3',
        'q4': 'c4',
        'q5': 'c5',
        'q6': 'c6',
        'q7': 'c7',
        'q8': 'c8',
    }

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

    @staticmethod
    def list_vars():
        return ['q1', 'q2', 'q3', 'q4']

    @staticmethod
    def list_obses():
        return ['l1', 'l2']

    @staticmethod
    def get_default_params():
        return {
            'debug': False,
            'sync': False,
        }

    def _get_var(self, var):
        debug = self.params['debug']
        if debug:
            print(f'get var {var}')
        dt = 2 * np.random.rand()  # 0 to 2s
        time.sleep(dt)
        val = self.interface.get_value(self.var_channel_map[var])
        if debug:
            print(f'done get var {var} as {val}')
            print(self.interface)
        return val

    def _set_var(self, var, x):
        debug = self.params['debug']
        if debug:
            print(f'set var {var} to {x}')
        dt = 2 * np.random.rand()  # 0 to 2s
        time.sleep(dt)
        self.interface.set_value(self.var_channel_map[var], x)
        if debug:
            val = self.interface.get_value(self.var_channel_map[var])
            print(f'done set var {var} to {val}')

    def _get_obs(self, obs):
        debug = self.params['debug']
        if debug:
            print(f'get obs {obs}')
        dt = 2 * np.random.rand()  # 0 to 2s
        time.sleep(dt)
        if obs == 'l1':
            values = self.interface.get_values(
                ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'])
            res = np.sum(np.abs(values))
        elif obs == 'l2':
            res = self.interface.get_value('norm')
        if debug:
            print(f'done get obs {obs} as {res}')
        return res
