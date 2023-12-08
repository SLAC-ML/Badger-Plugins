import numpy as np
from badger import environment


class Environment(environment.Environment):

    name = 'myenv'

    variables = {
        'x': [0, 1],
        'y': [0, 1],
        'z': [0, 1],
    }
    observables = ['norm', 'mean', 'norm_raw']

    # Environment parameters
    noise_level: float = 0.01
    num_raw: int = 120

    # Internal variables start with a single underscore
    _variables = {
        'x': 0,
        'y': 0,
        'z': 0,
    }

    def get_variables(self, variable_names: list[str]) -> dict:
        variable_outputs = {v: self._variables[v] for v in variable_names}

        return variable_outputs

    def set_variables(self, variable_inputs: dict[str, float]):
        for var, x in variable_inputs.items():
            self._variables[var] = x

    def get_observables(self, observable_names: list[str]) -> dict:
        x = self._variables['x']
        y = self._variables['y']
        z = self._variables['z']

        observable_outputs = {}
        for obs in observable_names:
            if obs == 'norm':
                observable_outputs[obs] = (x ** 2 + y ** 2 + z ** 2) ** 0.5
            elif obs == 'mean':
                observable_outputs[obs] = (x + y + z) / 3
            elif obs == 'norm_raw':
                norm = (x ** 2 + y ** 2 + z ** 2) ** 0.5
                signal = norm + \
                    self.noise_level * np.random.randn(self.num_raw)
                observable_outputs[obs] = signal.tolist()

        return observable_outputs

    def get_system_states(self):
        return {
            'Yo Yo!': 0.1,
            'Check it out': 'hahaha',
        }
