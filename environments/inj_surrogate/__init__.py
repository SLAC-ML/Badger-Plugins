import numpy as np
import os
import json
from badger import environment
from badger.interface import Interface


class Environment(environment.Environment):

    name = 'inj_surrogate'
    vranges = {
        'SOL1:solenoid_field_scale': [0.44, 0.55],
        'SQ01:b1_gradient': [-0.02, 0.02],
        'CQ01:b1_gradient': [-0.02, 0.02],
    }

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

        self.model = None
        self.variables = {
            'SOL1:solenoid_field_scale': 0.5,
            'SQ01:b1_gradient': 0,
            'CQ01:b1_gradient': 0,
        }
        self.observations = {
            'norm_emit_x': None,
            'norm_emit_y': None,
            'norm_emit': None,
        }
        # if the variables have been changed since the last model prediction
        self.modified = True

    @staticmethod
    def list_vars():
        return [
            'SOL1:solenoid_field_scale',
            'SQ01:b1_gradient',
            'CQ01:b1_gradient',
        ]

    @staticmethod
    def list_obses():
        return [
            'norm_emit_x',
            'norm_emit_y',
            'norm_emit',
        ]

    @staticmethod
    def get_default_params():
        env_root = os.path.dirname(os.path.realpath(__file__))

        return {
            'model_path': os.path.join(env_root, 'models'),
            'model_name': 'model_OTR2_NA_rms_emit_elu_2021-07-27T19_54_57-07_00',
            'model_info': os.path.join(env_root, 'configs', 'model_info.json'),
            'pv_info': os.path.join(env_root, 'configs', 'pv_info.json'),
            'ref_point': os.path.join(env_root, 'configs', 'ref_point.json'),
            'scaler_x': os.path.join(env_root, 'data', 'transformer_x.sav'),
            'scaler_y': os.path.join(env_root, 'data', 'transformer_y.sav'),
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
        self.observations['norm_emit_x'] = \
            nemit_x = y_out[:, model.loc_out['norm_emit_x']] * 1e6  # in um
        self.observations['norm_emit_y'] = \
            nemit_y = y_out[:, model.loc_out['norm_emit_y']] * 1e6  # in um
        self.observations['norm_emit'] = np.sqrt(nemit_x * nemit_y)  # in um

        return self.observations[obs]

    def load_model(self):
        # Lazy importing
        from .injector_surrogate_quads import Surrogate_NN

        self.model = model = Surrogate_NN(model_info_file=self.params['model_info'],
                                          pv_info_file=self.params['pv_info'])

        model.load_saved_model(model_path=self.params['model_path'],
                               model_name=self.params['model_name'])
        model.load_scaling(scalerfilex=self.params['scaler_x'],
                           scalerfiley=self.params['scaler_y'])
        model.take_log_out = False

        with open(self.params['ref_point'], 'r') as f:
            ref_point = json.load(f)
            ref_point = model.sim_to_machine(np.asarray(ref_point))
            self.ref_point = [ref_point[0]]  # nested list
