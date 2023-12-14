import time
import numpy as np
from badger import environment
from badger.interface import Interface
from badger.factory import get_intf


class Environment(environment.Environment):

    name = 'XFEL Sase1 Launch'

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

        # set interface according to params
        try:
            new_interface, _ = get_intf(params['interface'])
            self.interface = new_interface()
        except KeyError:
            print(f'Cannot load interface defined in params')

        self.limits_undulators = {}
        aircoil_list = ["XFEL.MAGNETS/MAGNET.ML/QF.2162.T2/CURRENT.SP",
                        "XFEL.MAGNETS/MAGNET.ML/QF.2177.T2/CURRENT.SP",
                        "XFEL.MAGNETS/MAGNET.ML/QF.2192.T2/CURRENT.SP",
                        "XFEL.MAGNETS/MAGNET.ML/QF.2207.T2/CURRENT.SP",
                        "XFEL.MAGNETS/MAGNET.ML/QF.2218.T2/CURRENT.SP"
                        ]
        for addr in aircoil_list:
            self.limits_undulators[addr]  = [20, 60]
        

    def _get_vrange(self, var):
        return self.limits_undulators[var]

    @staticmethod
    def list_vars():
        return ["XFEL.MAGNETS/MAGNET.ML/QF.2162.T2/CURRENT.SP",
                "XFEL.MAGNETS/MAGNET.ML/QF.2177.T2/CURRENT.SP",
                "XFEL.MAGNETS/MAGNET.ML/QF.2192.T2/CURRENT.SP",
                "XFEL.MAGNETS/MAGNET.ML/QF.2207.T2/CURRENT.SP",
                "XFEL.MAGNETS/MAGNET.ML/QF.2218.T2/CURRENT.SP"
                ]
    

    # TODO: add losses
    @staticmethod
    def list_obses():
        return ['sases_average']

    @staticmethod
    def get_default_params():
        return {
            'waiting_time': 15,
            'interface': 'doocs'
        }

    def _get_var(self, var):
        return self.interface.get_value(var)

    def _set_var(self, var, x):
        self.interface.set_value(var, x)

    def _get_obs(self, obs):
        try:
            dt = self.params['waiting_time']
        except KeyError:
            dt = 0
        time.sleep(dt)



        if obs == 'sases_average':
            values = []
            for i in range(30):
                sa1 = self.interface.get_value(
                    "XFEL.FEL/XGM/XGM.2643.T9/INTENSITY.SA1.RAW.TRAIN")
                values.append(sa1)
                time.sleep(0.1)
            return np.mean(values)
