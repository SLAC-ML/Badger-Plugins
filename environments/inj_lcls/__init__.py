from typing import Dict, List
from badger import environment
from .emit_launch.emit_ctrl_class import Emit_Meas


class Environment(environment.Environment):

    name = 'inj_lcls'
    variables = {
        'SOLN:IN20:121:BCTRL': [0.44, 0.55],  # solenoid
        'QUAD:IN20:121:BCTRL': [-0.02, 0.02],  # skew quad
        'QUAD:IN20:122:BCTRL': [-0.02, 0.02],  # skew qaud
        'QUAD:IN20:525:BCTRL': [-5.0, -3.0],  # Q525
        'QUAD:IN20:511:BCTRL': [2.0, 7.0],  # Q511
        'QUAD:IN20:441:BCTRL': [-1.0, 2.0],  # Q441
        'QUAD:IN20:425:BCTRL': [-4.0, -1.0],  # Q425
        'QUAD:IN20:371:BCTRL': [2.5, 2.9],  # Q371
        'QUAD:IN20:361:BCTRL': [-3.5, -2.75],  # Q361
    }
    observables = [
        'emit',
    ]

    _em = None

    def get_variables(self, variable_names: List[str]) -> Dict:
        assert self.interface, 'Must provide an interface!'

        variable_outputs = self.interface.get_values(variable_names)

        return variable_outputs

    def set_variables(self, variable_inputs: Dict[str, float]):
        assert self.interface, 'Must provide an interface!'

        self.interface.set_values(variable_inputs)

    def get_observables(self, observable_names: List[str]) -> Dict:
        assert self.interface, 'Must provide an interface!'

        observable_outputs = {}
        for obs in observable_names:
            if obs == 'emit':
                if self._em is None:  # lazy loading
                    self._em = Emit_Meas()

                value = self._em.launch_emittance_measurment()
            else:
                value = None
            observable_outputs[obs] = value

        return observable_outputs
