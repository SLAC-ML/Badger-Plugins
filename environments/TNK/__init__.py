import numpy as np
from badger import environment
from badger.interface import Interface


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

    @staticmethod
    def list_vars():
        return ['x1', 'x2']

    @staticmethod
    def list_obses():
        return ['y1', 'y2', 'c1', 'c2', 'some_array']

    @staticmethod
    def get_default_params():
        return None

    def _get_vrange(self, var):
        return [0, 3.14159]

    def _get_var(self, var):
        return self.variables[var]

    def _set_var(self, var, x):
        self.variables[var] = x

        # Filling up the observations
        ind = [self.variables['x1'], self.variables['x2']]
        objectives, constraints = TNK(ind)
        self.observations['y1'] = objectives[0]
        self.observations['y2'] = objectives[1]
        self.observations['c1'] = constraints[0]
        self.observations['c2'] = constraints[1]

    def _get_obs(self, obs):
        return self.observations[obs]
