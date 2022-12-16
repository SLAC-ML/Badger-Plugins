import time
import numpy as np
from badger import environment
from badger.interface import Interface
import pathlib



class Knobs():
    def __init__(self, csv_file_name):
        self._matrix = self.load_skrew_knob_from_csv(csv_file_name)
        # there are no names in csv so generate names
        self._row_names = [f"knob-{i}" for i in range(self.get_count())]

    @staticmethod
    def load_skrew_knob_from_csv(filename) -> np.ndarray:
        return np.genfromtxt(filename, delimiter=',')

    def get_count(self):
        return self._matrix.shape[0]

    def get_names(self):
        return self._row_names

    def gen_matrix(self, vars):
        if len(vars) == len(self._row_names):
            return self._matrix
        vars_hash = set(vars)
        remove_row_idx = [idx for idx, name in enumerate(self._row_names) if not name in vars_hash]
        return np.delete(self._matrix, remove_row_idx, axis=0) # remove rows



class Environment(environment.Environment):
    path = pathlib.Path(__file__).parent.resolve()
    knobs = Knobs(path / "data" / "SkewKnobSF2A.csv")
    name = 'esrf_skew_knob'

    def __init__(self, interface: Interface, params):
        self.limits_knobs = { name : [-1, 1] for name in Environment.knobs.get_names()}
        self.current_vars = []
        super().__init__(interface, params)

    def _get_vrange(self, var):
        return self.limits_knobs[var]

    @staticmethod
    def list_vars():
        return Environment.knobs.get_names()
    
    # TODO: add losses
    @staticmethod
    def list_obses():
        return ['emittance']

    @staticmethod
    def get_default_params():
        return {
            'waiting_time': 1,
        }

    def _get_var(self, var):
        raise Exception("values have to be get at once!")

    def _get_vars(self, vars):
        print(f"requested values: {vars}")
        if len(self.current_vars) == 0:
            self.current_vars = [0.0 for _ in range(len(vars))]     
        return self.current_vars

    def _set_var(self, var, x): 
        raise Exception("values have to be set at once!")

    def _set_vars(self, vars, _x):
        self.current_vars = _x
        print(f"value names {vars}")
        skews = np.sum(_x * np.transpose(Environment.knobs.gen_matrix(vars)), axis=1)
        self.interface.set_value(channel='srmag/sqp/all', attr='CorrectionStrengths', value=skews) 

    def _get_obs(self, obs):
        try:
            dt = self.params['waiting_time']
        except KeyError:
            dt = 0
        time.sleep(dt)


        if obs == 'emittance':
            return self.interface.get_value('srdiag/emittance/id07/Emittance_V')

