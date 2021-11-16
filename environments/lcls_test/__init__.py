from badger import environment
from badger.interface import Interface


class Environment(environment.Environment):

    name = 'lcls_test'
    vranges = {
        'SOLN:IN20:121:BCTRL': [0.44, 0.55],
        'QUAD:IN20:121:BCTRL': [-0.02, 0.02],
        'QUAD:IN20:122:BCTRL': [-0.02, 0.02],
        'QUAD:IN20:371:BCTRL': [2.5, 2.9],
        'QUAD:IN20:361:BCTRL': [-3.5, -2.75],
    }

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

        self.pv_limits = {}
        self.update_pvs_limits()

    @staticmethod
    def list_vars():
        return [
            'SOLN:IN20:121:BCTRL',  # solenoid
            'QUAD:IN20:121:BCTRL',  # skew quad
            'QUAD:IN20:122:BCTRL',  # skew qaud
            'QUAD:IN20:371:BCTRL',  # Q371
            'QUAD:IN20:361:BCTRL',  # Q361
        ]

    @staticmethod
    def list_obses():
        return ['SIOC:SYS0:ML00:CALC252']

    @staticmethod
    def get_default_params():
        return None

    @classmethod
    def _get_vrange(cls, var):
        return cls.vranges[var]

    def _get_var(self, var):
        # TODO: update pv limits every time?
        return self.interface.get_value(var)

    def _set_var(self, var, x):
        self.interface.set_value(var, x)

    def _get_obs(self, obs):
        return self.interface.get_value(obs)

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
