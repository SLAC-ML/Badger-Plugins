import os.path
import time
from typing import Dict, List

import yaml
from badger import environment
from .screen_diagnostic import ImageDiagnostic
from pydantic import validator


class Environment(environment.Environment):
    name = 'lcls_injector'
    variables = {
        # 'SOLN:IN20:121:BCTRL': [0.44, 0.55],
        # 'QUAD:IN20:121:BCTRL': [-0.02, 0.02],
        # 'QUAD:IN20:122:BCTRL': [-0.02, 0.02],
        'QUAD:IN20:525:BCTRL': [-5.0, -3.0],
        #'QUAD:IN20:511:BCTRL': [2.0, 7.0],
        # 'QUAD:IN20:441:BCTRL': [-1.0, 2.0],
        # 'QUAD:IN20:425:BCTRL': [-4.0, -1.0],
        # 'QUAD:IN20:371:BCTRL': [2.5, 2.9],
        # 'QUAD:IN20:361:BCTRL': [-3.5, -2.75],
    }
    observables = ["Sx", "Sy", "Cx", "Cy", "charge"]

    # environment parameters
    diagnostic: ImageDiagnostic
    measurement_delay: float = 3.0
    run_dir: str = None

    @validator("diagnostic", pre=True)
    def validate_diagnostic(cls, v):
        path = os.path.split(__file__)[0]
        if isinstance(v, ImageDiagnostic):
            return v
        else:
            # load correct config file from yaml
            config_file = {"OTR3": os.path.join(path, "OTR3_config.yml")}
            diagnostic_config = yaml.safe_load(open(config_file[v]))
            return ImageDiagnostic.parse_obj(diagnostic_config)

    def set_variables(self, variable_inputs: Dict[str, float]):
        self.interface.set_values(variable_inputs)
        time.sleep(self.measurement_delay)

    def get_variables(self, variable_names: List[str]) -> Dict:
        return self.interface.get_values(variable_names)

    def get_observables(self, observable_names: List[str]) -> Dict:
        assert self.interface, 'Must provide an interface!'

        # make set out of observable names
        observable_names = set(observable_names)

        # take screen image if observable is requested
        diagnostic_observables = ["Sx", "Sy", "Cx", "Cy"]
        measure_image = False
        for ele in diagnostic_observables:
            if ele in observable_names:
                observable_names.remove(ele)
                measure_image = True

        if measure_image:
            self.diagnostic.save_image_location = self.run_dir
            image_results = self.diagnostic.measure_beamsize(1)
        else:
            image_results = {}

        outputs = image_results

        # add PV measurements
        pv_mapping = {"charge": "SIOC:SYS0:ML00:CALC252"}
        for observable in observable_names:
            outputs[observable] = self.interface.get_value(pv_mapping[observable])

        return outputs



