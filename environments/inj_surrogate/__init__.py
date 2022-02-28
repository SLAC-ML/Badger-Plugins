import numpy as np
import os
import json
from badger import environment
from badger.interface import Interface


class Environment(environment.Environment):

    name = 'inj_surrogate'
    vranges = {
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

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

        self.model = None
        self.variables = {
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
        self.observations = {
            'sigma_x': None,
            'sigma_y': None,
            'sigma_z': None,
            'norm_emit_x': None,
            'norm_emit_y': None,
            'norm_emit': None,
        }

        env_root = os.path.dirname(os.path.realpath(__file__))
        self._paths = {
            'model_path': os.path.join(env_root, 'models'),
            'model_info': os.path.join(env_root, 'configs', 'model_info.json'),
            'pv_info': os.path.join(env_root, 'configs', 'pv_info.json'),
            'ref_point': os.path.join(env_root, 'configs', 'ref_point.json'),
            'scaler_x': os.path.join(env_root, 'data', 'transformer_x.sav'),
            'scaler_y': os.path.join(env_root, 'data', 'transformer_y.sav'),
        }

        # if the variables have been changed since the last model prediction
        self.modified = True

    @staticmethod
    def list_vars():
        return [
            'distgen:r_dist:sigma_xy:value',
            'distgen:t_dist:length:value',
            'distgen:total_charge:value',
            'SOL1:solenoid_field_scale',
            'CQ01:b1_gradient',
            'SQ01:b1_gradient',
            'L0A_scale:voltage',
            'L0A_phase:dtheta0_deg',
            'L0B_scale:voltage',
            'L0B_phase:dtheta0_deg',
            'QA01:b1_gradient',
            'QA02:b1_gradient',
            'QE01:b1_gradient',
            'QE02:b1_gradient',
            'QE03:b1_gradient',
            'QE04:b1_gradient'
        ]

    @staticmethod
    def list_obses():
        return [
            'sigma_x',
            'sigma_y',
            'sigma_z',
            'norm_emit_x',
            'norm_emit_y',
            'norm_emit',
        ]

    @staticmethod
    def get_default_params():
        return {
            'model_name': 'model_OTR2_NA_rms_emit_elu_2021-07-27T19_54_57-07_00',
        }

    def _get_vrange(self, var):
        return self.vranges[var]

    def _get_var(self, var):
        x = self.variables[var]

        return x

    def _set_var(self, var, x):
        if self.variables[var] != x:
            self.variables[var] = x
            self.modified = True

    def _get_obs(self, obs):
        if not self.modified:
            return self.observations[obs]

        # Lazy loading
        if self.model is None:
            self.load_model()

        self.modified = False

        # Predict with model
        model = self.model

        # Make input array of length model_in_list (inputs model takes)
        x_in = np.empty((1, len(model.model_in_list)))

        # Fill in reference point around which to optimize
        x_in[:, :] = np.asarray(self.ref_point)

        # Set solenoid, SQ, CQ to values from optimization step
        for var in self.list_vars():
            x_in[:, model.loc_in[var]] = self.variables[var]

        # Output predictions
        y_out = model.pred_machine_units(x_in)
        self.observations['sigma_x'] = \
            y_out[:, model.loc_out['sigma_x']] * 1e3  # in mm
        self.observations['sigma_y'] = \
            y_out[:, model.loc_out['sigma_y']] * 1e3  # in mm
        self.observations['sigma_z'] = \
            y_out[:, model.loc_out['sigma_z']] * 1e3  # in mm?
        self.observations['norm_emit_x'] = \
            nemit_x = y_out[:, model.loc_out['norm_emit_x']] * 1e6  # in um
        self.observations['norm_emit_y'] = \
            nemit_y = y_out[:, model.loc_out['norm_emit_y']] * 1e6  # in um
        self.observations['norm_emit'] = np.sqrt(nemit_x * nemit_y)  # in um

        return self.observations[obs]

    def load_model(self):
        # Lazy importing
        from .injector_surrogate_quads import Surrogate_NN

        self.model = model = Surrogate_NN(model_info_file=self._paths['model_info'],
                                          pv_info_file=self._paths['pv_info'])

        model.load_saved_model(model_path=self._paths['model_path'],
                               model_name=self.params['model_name'])
        model.load_scaling(scalerfilex=self._paths['scaler_x'],
                           scalerfiley=self._paths['scaler_y'])
        model.take_log_out = False

        with open(self._paths['ref_point'], 'r') as f:
            ref_point = json.load(f)
            ref_point = model.sim_to_machine(np.asarray(ref_point))
            self.ref_point = [ref_point[0]]  # nested list
