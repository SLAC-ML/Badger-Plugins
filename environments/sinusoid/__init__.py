import numpy as np
from typing import Dict
from badger import environment


class Environment(environment.Environment):

    name = 'sinusoid'
    variables = {
        'x1': [0, 1.75 * 3.14159],
    }
    observables = ['y1', 'c1']

    _variables = {
        'x1': 0.0,
    }
    _observations = {
        'y1': None,
        'c1': None,
    }

    def get_variables(self, variable_names):
        variable_outputs = {v: self._variables[v] for v in variable_names}

        return variable_outputs

    def set_variables(self, variable_inputs: Dict[str, float]):
        for var, x in variable_inputs.items():
            self._variables[var] = x

        # Filling up the observations
        x1 = self._variables['x1']

        self._observations['y1'] = np.sin(x1)
        self._observations['c1'] = 10 * np.sin(x1) - 9.5 + np.sin(7.0 * x1)

    def get_observables(self, observable_names):
        return {k: self._observations[k] for k in observable_names}
