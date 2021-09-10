import numpy as np
from badger import environment
from badger.interface import Interface
from badger.utils import denorm
from operator import itemgetter
import logging


# Pure number version
def TNK(individual):
    x1 = individual[0]
    x2 = individual[1]
    objectives = (x1, x2)
    constraints = (x1 ** 2 + x2 ** 2 - 1.0 - 0.1 * np.cos(16 *
                   np.arctan2(x1, x2)), (x1 - 0.5) ** 2 + (x2 - 0.5) ** 2)
    return objectives, constraints


class Environment(environment.Environment):

    name = 'TNK'
    BOUND_LOW, BOUND_UP = [0.0, 0.0], [3.14159, 3.14159]

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

        self.variables = {
            'x1': 0,
            'x2': 0,
        }
        self.observations = {
            'y1': None,
            'y2': None,
            'c1': None,
            'c2': None,
            'some_array': np.array([1, 2, 3]),
        }

    def get_var(self, var):
        try:
            value = self.variables[var]
        except KeyError:
            logging.warn(f'Variable {var} doesn\'t exist!')
            value = None

        return value

    def set_var(self, var, x):
        if var not in self.variables.keys():
            logging.warn(f'Variable {var} doesn\'t exist!')
            return

        self.variables[var] = x

        # Filling up the observations
        ind = [
            denorm(self.variables['x1'], self.BOUND_LOW[0], self.BOUND_UP[0]),
            denorm(self.variables['x2'], self.BOUND_LOW[1], self.BOUND_UP[1]),
        ]
        objectives, constraints = TNK(ind)
        self.observations['y1'] = objectives[0]
        self.observations['y2'] = objectives[1]
        self.observations['c1'] = constraints[0]
        self.observations['c2'] = constraints[1]

    def get_obs(self, obs):
        try:
            value = self.observations[obs]
        except KeyError:
            logging.warn(f'Unsupported observation {obs}')
            value = None

        return value
