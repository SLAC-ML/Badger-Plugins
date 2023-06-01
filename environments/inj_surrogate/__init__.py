import numpy as np
from typing import Dict
import os
import time
import json
from badger import environment


class Environment(environment.Environment):

    name = 'inj_surrogate'
    variables = {
        'distgen:r_dist:sigma_xy:value': [0.6306, 1.5000],
        'distgen:t_dist:length:value': [1.8182, 7.2719],
        'distgen:total_charge:value': [250.0000, 250.0000],
        'SOL1:solenoid_field_scale': [0.3774, 0.4984],
        'CQ01:b1_gradient': [-0.0210, 0.0210],
        'SQ01:b1_gradient': [-0.0210, 0.0210],
        'L0A_scale:voltage': [58.0000, 58.0000],
        'L0A_phase:dtheta0_deg': [-24.9987, 9.9918],
        'L0B_scale:voltage': [70.0000, 70.0000],
        'L0B_phase:dtheta0_deg': [-24.9997, 9.9989],
        'QA01:b1_gradient': [-4.3181, -1.0800],
        'QA02:b1_gradient': [1.0914, 4.3097],
        'QE01:b1_gradient': [-7.5598, -1.0808],
        'QE02:b1_gradient': [-1.0782, 7.5599],
        'QE03:b1_gradient': [-1.0792, 7.5583],
        'QE04:b1_gradient': [-7.5579, -1.0800],
    }
    observables = [
        'sigma_x',
        'sigma_y',
        'sigma_z',
        'norm_emit_x',
        'norm_emit_y',
        'norm_emit',
    ]

    model_name: str = 'model_OTR2_NA_rms_emit_elu_2021-07-27T19_54_57-07_00'
    waiting_time: float = 0

    _variables = {
        'distgen:r_dist:sigma_xy:value': 1.2716,
        'distgen:t_dist:length:value': 1.8551,
        'distgen:total_charge:value': 250.0000,
        'SOL1:solenoid_field_scale': 0.4780,
        'CQ01:b1_gradient': -0.0015,
        'SQ01:b1_gradient': -0.0007,
        'L0A_scale:voltage': 58.0000,
        'L0A_phase:dtheta0_deg': -9.5360,
        'L0B_scale:voltage': 70.0000,
        'L0B_phase:dtheta0_deg': 9.8557,
        'QA01:b1_gradient': -2.0006,
        'QA02:b1_gradient': 2.0006,
        'QE01:b1_gradient': -0.2022,
        'QE02:b1_gradient': -0.1794,
        'QE03:b1_gradient': 2.8522,
        'QE04:b1_gradient': -3.2184,
    }
    _observations = {
        'sigma_x': None,
        'sigma_y': None,
        'sigma_z': None,
        'norm_emit_x': None,
        'norm_emit_y': None,
        'norm_emit': None,
    }
    _model = None
    _ref_point = None
    _modified = True
    _env_root = os.path.dirname(os.path.realpath(__file__))
    _paths = {
        'model_path': os.path.join(_env_root, 'models'),
        'model_info': os.path.join(_env_root, 'configs', 'model_info.json'),
        'pv_info': os.path.join(_env_root, 'configs', 'pv_info.json'),
        'ref_point': os.path.join(_env_root, 'configs', 'ref_point.json'),
        'scaler_x': os.path.join(_env_root, 'data', 'transformer_x.sav'),
        'scaler_y': os.path.join(_env_root, 'data', 'transformer_y.sav'),
    }

    def get_variables(self, variable_names):
        variable_outputs = {v: self._variables[v] for v in variable_names}

        return variable_outputs

    def set_variables(self, variable_inputs: Dict[str, float]):
        for var, x in variable_inputs.items():
            if self._variables[var] != x:
                self._variables[var] = x
                self._modified = True

    def get_observables(self, observable_names):
        dt = self.waiting_time
        time.sleep(dt)

        if not self._modified:
            return {k: self._observations[k] for k in observable_names}

        # Lazy loading
        if self._model is None:
            self.load_model()

        self._modified = False

        # Predict with model
        model = self._model

        assert model is not None, 'Model failed to initialize!'

        # Make input array of length model_in_list (inputs model takes)
        x_in = np.empty((1, len(model.model_in_list)))

        # Fill in reference point around which to optimize
        x_in[:, :] = np.asarray(self._ref_point)

        # Set solenoid, SQ, CQ to values from optimization step
        for var in self.variable_names:
            x_in[:, model.loc_in[var]] = self._variables[var]

        # Update predictions
        y_out = model.pred_machine_units(x_in)
        self._observations['sigma_x'] = \
            y_out[:, model.loc_out['sigma_x']] * 1e3  # in mm
        self._observations['sigma_y'] = \
            y_out[:, model.loc_out['sigma_y']] * 1e3  # in mm
        self._observations['sigma_z'] = \
            y_out[:, model.loc_out['sigma_z']] * 1e3  # in mm?
        self._observations['norm_emit_x'] = \
            nemit_x = y_out[:, model.loc_out['norm_emit_x']] * 1e6  # in um
        self._observations['norm_emit_y'] = \
            nemit_y = y_out[:, model.loc_out['norm_emit_y']] * 1e6  # in um
        self._observations['norm_emit'] = np.sqrt(nemit_x * nemit_y)  # in um

        return {k: self._observations[k] for k in observable_names}

    def load_model(self):
        # Lazy importing
        from .injector_surrogate_quads import Surrogate_NN

        self._model = model = Surrogate_NN(model_info_file=self._paths['model_info'],
                                           pv_info_file=self._paths['pv_info'])

        model.load_saved_model(model_path=self._paths['model_path'],
                               model_name=self.model_name)
        model.load_scaling(scalerfilex=self._paths['scaler_x'],
                           scalerfiley=self._paths['scaler_y'])
        model.take_log_out = False

        with open(self._paths['ref_point'], 'r') as f:
            ref_point = json.load(f)
            ref_point = model.sim_to_machine(np.asarray(ref_point))
            self._ref_point = [ref_point[0]]  # nested list
