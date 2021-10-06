from badger import environment
from badger.interface import Interface
from .emit_launch.emit_ctrl_class import Emit_Meas


class Environment(environment.Environment):

    name = 'inj_lcls'
    vranges = {
        'SOLN:IN20:121:BCTRL': [0.44, 0.55],
        'QUAD:IN20:121:BCTRL': [-0.02, 0.02],
        'QUAD:IN20:122:BCTRL': [-0.02, 0.02],
        'QUAD:IN20:525:BCTRL': [-5.0, -3.0],
        'QUAD:IN20:511:BCTRL': [2.0, 7.0],
        'QUAD:IN20:441:BCTRL': [-1.0, 2.0],
        'QUAD:IN20:425:BCTRL': [-4.0, -1.0],
        'QUAD:IN20:371:BCTRL': [2.5, 2.9],
        'QUAD:IN20:361:BCTRL': [-3.5, -2.75],
    }

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

        self.em = Emit_Meas()

        self.pv_limits = {}
        self.update_pvs_limits()

    @staticmethod
    def list_vars():
        return [
            'SOLN:IN20:121:BCTRL',  # solenoid
            'QUAD:IN20:121:BCTRL',  # skew quad
            'QUAD:IN20:122:BCTRL',  # skew qaud
            'QUAD:IN20:525:BCTRL',  # Q525
            'QUAD:IN20:511:BCTRL',  # Q511
            'QUAD:IN20:441:BCTRL',  # Q441
            'QUAD:IN20:425:BCTRL',  # Q425
            'QUAD:IN20:371:BCTRL',  # Q371
            'QUAD:IN20:361:BCTRL',  # Q361
        ]

    @staticmethod
    def list_obses():
        return ['emit']

    @staticmethod
    def get_default_params():
        return None

    @classmethod
    def _get_vrange(cls, var):
        return cls.vranges[var]

    def _get_var(self, var):
        raw_value = self.interface.get_value(var)

        return raw_value

    def _set_var(self, var, x):
        self.interface.set_value(var, x)

    def _get_obs(self, obs):
        if obs == 'emit':
            emit = self.em.launch_emittance_measurment()

            return emit

    def update_pv_limits(self, eid):
        if eid.endswith(':BACT') or eid.endswith(':BCTRL'):
            prefix = eid[:eid.rfind(':') + 1]
        else:
            prefix = eid + ':'
        # pv_set = prefix + 'BCTRL'
        # pv_read = prefix + 'BACT'
        pv_low = prefix + 'BCTRL.DRVL'
        pv_high = prefix + 'BCTRL.DRVH'
        low = self.interface.get_value(pv_low)
        high = self.interface.get_value(pv_high)
        self.pv_limits[eid] = (low, high)

    def update_pvs_limits(self):
        for eid in self.list_vars():
            self.update_pv_limits(eid)
