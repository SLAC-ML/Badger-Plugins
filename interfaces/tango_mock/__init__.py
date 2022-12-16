import pathlib
import numpy as np
import at
from badger import interface


class Interface(interface.Interface):
    name = 'tango_mock'

    def __init__(self, params=None):
        super().__init__(params)
        path = pathlib.Path(__file__).parent.resolve()
        self.ring = at.load_mat(path / 'model' / 'betamodel.mat', mat_key='betamodel')
        self.indskew = at.get_refpts(self.ring, 'S[HFDIJ]*')
        self.ring.radiation_on()
        self.sqpinput = 0.01*np.random.rand((288))*10e-3

    @staticmethod
    def get_default_params():
        return None

    def get_value(self, channel: str, attr=None):
        print('Called get_value for channel: {}.'.format(channel))
        if channel == 'srdiag/emittance/id07/Emittance_V':
            _, beamdata1, _ = at.ohmi_envelope(self.ring)
            vert_emitt=beamdata1.mode_emittances[1]
            return vert_emitt

        raise KeyError(f"Channel {channel} is unknown.")

    def set_value(self, channel: str, attr: str, value):
        print("Called set_value for channel: {}, with value: {}".format(channel, value))
        if channel == 'srmag/sqp/all':
            print(f"value: {type(value)}")
            print(f"sqpinput: {type(self.sqpinput)}")
            at.set_value_refpts(self.ring, self.indskew, 'PolynomA', value + self.sqpinput, 1)
            return
        raise KeyError(f"Channel {channel} is unknown.")
    