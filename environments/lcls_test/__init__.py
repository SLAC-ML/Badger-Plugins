from badger import environment
from badger.interface import Interface


class Environment(environment.Environment):

    name = 'lcls_test'
    # vranges = {
    #     'SOLN:IN20:121:BCTRL': [0, 0.55],
    #     'QUAD:IN20:121:BCTRL': [-0.015, 0.015],
    #     'QUAD:IN20:122:BCTRL': [-0.015, 0.015],
    #     'QUAD:IN20:371:BCTRL': [-20, 20],
    #     'QUAD:IN20:361:BCTRL': [-20, 20],
    # }

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

        self.pv_limits = {}
        # self.update_pvs_limits()

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

    def _get_vrange(self, var):
        try:
            vrange = self.pv_limits[var]
        except KeyError:
            self.update_pv_limits(var)
            vrange = self.pv_limits[var]

        return vrange

    def _get_var(self, var):
        # TODO: update pv limits every time?
        if var.endswith(':BCTRL'):
            prefix = var[:var.rfind(':')]
            readback = prefix + ':BACT'
        else:
            readback = var

        return self.interface.get_value(readback)

    def _set_var(self, var, x):
        self.interface.set_value(var, x)

    def _check_var(self, var):
        if not var.endswith(':BCTRL'):
            return 0

        prefix = var[:var.rfind(':')]
        flag = prefix + ':STATCTRLSUB.T'
        return self.interface.get_value(flag)

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
