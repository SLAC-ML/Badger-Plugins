import time
import numpy as np
from typing import Dict, List
from badger import environment


class Environment(environment.Environment):

    name = 'silly'
    variables = {
        'q1': [0, 1],
        'q2': [0, 1],
        'q3': [0, 1],
        'q4': [0, 1],
    }
    observables = ['l1', 'l2']

    # Env params
    chaos: bool = False

    # Private properties
    _var_channel_map: Dict = {
        'q1': 'c1',
        'q2': 'c2',
        'q3': 'c3',
        'q4': 'c4',
        'q5': 'c5',
        'q6': 'c6',
        'q7': 'c7',
        'q8': 'c8',
    }

    def get_variables(self, variable_names: List[str]) -> Dict:
        if self.interface is None:
            raise Exception('Must provide an interface!')

        channel_names = [self._var_channel_map[v] for v in variable_names]
        channel_outputs = self.interface.get_values(channel_names)

        variable_outputs = {v: channel_outputs[self._var_channel_map[v]]
                            for v in variable_names}

        return variable_outputs

    def set_variables(self, variable_inputs: Dict[str, float]):
        if self.interface is None:
            raise Exception('Must provide an interface!')

        channel_inputs = {self._var_channel_map[k]: v
                          for k, v in variable_inputs.items()}

        self.interface.set_values(channel_inputs)

        # Emulate the real environment w/ communication lags
        if not self.chaos:
            return

        timeout = 3  # second
        time_start = time.time()
        while round(np.random.rand()):
            time.sleep(0.1 * np.random.rand())

            time_elapsed = time.time() - time_start
            if time_elapsed > timeout:
                break

    def get_observables(self, observable_names: List[str]) -> Dict:
        if self.interface is None:
            raise Exception('Must provide an interface!')

        observable_outputs = {}
        for obs in observable_names:
            if obs == 'l1':
                outputs = self.interface.get_values(
                    ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'])
                observable_outputs[obs] = np.sum(np.abs(list(outputs.values())))
            elif obs == 'l2':
                observable_outputs[obs] = self.interface.get_values(['norm'])['norm']

        return observable_outputs
