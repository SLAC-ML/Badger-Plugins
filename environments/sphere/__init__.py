import torch
from typing import Dict
from badger import environment


class Environment(environment.Environment):

    name = 'sphere'
    variables = {f'x{i}': [-1, 1] for i in range(20)}
    observables = ['f']

    _variables = {f'x{i}': 0.0 for i in range(20)}
    _observations = {
        'f': None,
    }

    def get_variables(self, variable_names):
        variable_outputs = {v: self._variables[v] for v in variable_names}

        return variable_outputs

    def set_variables(self, variable_inputs: Dict[str, float]):
        for var, x in variable_inputs.items():
            self._variables[var] = x

        # Filling up the observations
        x = torch.tensor([self._variables[f'x{i}'] for i in range(20)])

        self._observations['f'] = (x ** 2).sum().numpy()

    def get_observables(self, observable_names):
        return {k: self._observations[k] for k in observable_names}
