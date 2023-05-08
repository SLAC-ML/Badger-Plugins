import numpy as np
import os
from badger import environment
from badger.interface import Interface
from .utils import k_taper, taper_output


class Environment(environment.Environment):
    name = "lcls_taper"

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

        self.variables = {
            "a": 0.06,
            "split_ix": 80,
            "powr": 2,
        }
        self.observations = {
            "power": None,
        }
        self.z = None
        self.power = None

        env_root = os.path.dirname(os.path.realpath(__file__))
        particle_pos_file = os.path.join(
            env_root, "data", self.params["particle_pos"]
        )
        self.DEFAULT_INPUT = dict(
            npart=512,  # n-macro-particles per bucket
            s_steps=200,  # n-sample points along bunch length
            z_steps=200,  # n-sample points along undulator
            energy=4313.34e6,  # electron energy [eV]
            eSpread=0,  # relative rms energy spread [1]
            emitN=1.2e-6,  # normalized transverse emittance [m-rad]
            currentMax=3900,  # peak current [Ampere]
            beta=26,  # mean beta [meter]
            unduPeriod=0.03,  # undulator period [meter]
            unduK=np.full(200, 3.5),  # undulator parameter, K [1], array could taper.
            unduL=70,  # length of undulator [meter]
            radWavelength=None,  # Will calculate based on resonance condition for unduK[0]
            random_seed=31,  # for reproducibilit
            particle_position=np.genfromtxt(
                particle_pos_file, delimiter=","
            ),  # or None
            hist_rule="square-root",  # 'square-root' or 'sturges' or 'rice-rule' or 'self-design', number \                                       #  of intervals to generate the histogram of eta value in a bucket
            iopt="sase",
        )

        # if the variables have been changed since the last model prediction
        self.modified = True

    @staticmethod
    def list_vars():
        return [
            "a",
            "split_ix",
            "powr",
        ]

    @staticmethod
    def list_obses():
        return [
            "power",
        ]

    @staticmethod
    def get_default_params():
        return {
            "particle_pos": "SASE_particle_position.csv",
            "k0": 3.5,
            "n": 200,
        }

    def _get_vrange(self, var):
        if var == "a":
            return [0, 0.5]
        elif var == "split_ix":
            n = self.params["n"]
            return [int(0.25 * n), int(0.75 * n)]
        elif var == "powr":
            return [1.9, 2.1]

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

        # Run the simulation
        try:
            K = k_taper(k0=self.params['k0'], n=int(self.params['n']),
                        a=self.variables['a'],
                        split_ix=int(self.variables['split_ix']),
                        powr=self.variables['powr'])
            self.z, self.power = taper_output(K, self.DEFAULT_INPUT)

            self.modified = False

            # Update the observations
            self.observations["power"] = self.power[-1] * 1e-9  # unit: GW
        except Exception as e:
            print(e)

        return self.observations[obs]
