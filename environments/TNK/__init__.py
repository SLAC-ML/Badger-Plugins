import numpy as np
from typing import Dict
from badger import environment


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
    variables = {
        'x1': [0, 3.14159],
        'x2': [0, 3.14159],
    }
    observables = ['y1', 'y2', 'c1', 'c2', 'some_array']

    _variables = {
        'x1': 0.0,
        'x2': 0.0,
    }
    _observations = {
        'y1': None,
        'y2': None,
        'c1': None,
        'c2': None,
        'some_array': np.array([1, 2, 3]),
    }

    def get_variables(self, variable_names):
        variable_outputs = {v: self._variables[v] for v in variable_names}

        return variable_outputs

    def set_variables(self, variable_inputs: Dict[str, float]):
        for var, x in variable_inputs.items():
            self._variables[var] = x

        # Filling up the observations
        ind = [self._variables['x1'], self._variables['x2']]
        objectives, constraints = TNK(ind)
        self._observations['y1'] = objectives[0]
        self._observations['y2'] = objectives[1]
        self._observations['c1'] = constraints[0]
        self._observations['c2'] = constraints[1]

    def get_observables(self, observable_names):
        return {k: self._observations[k] for k in observable_names}
