import time
import numpy as np
from badger import environment
from badger.interface import Interface
from badger.factory import get_intf

def get_aircoil_address(magnet_name: str, number: int) -> str:
    return f'XFEL.FEL/UNDULATOR.SASE3/{magnet_name}.CELL{number}.SA3/FIELD.OFFSET'

def get_aircoil_list() -> list:
    vars_list = [] 
    for i in range(1, 27):
        if i in [13]: 
            continue        # skip missing cells
        for m in ['CAX', 'CAY', 'CBX', 'CBY']:
            addr = get_aircoil_address(m, i)
            vars_list.append(addr)
    return vars_list



class Environment(environment.Environment):

    name = 'XFEL Sase3 Aircoils'

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)


        # set interface according to params
        try:
            new_interface, _ = get_intf(params['interface'])
            self.interface = new_interface()
        except KeyError:
            print(f'Cannot load interface defined in params')

        self.limits_undulators = {}
        aircoil_list = get_aircoil_list()
        for addr in aircoil_list:
            self.limits_undulators[addr]  = [-0.5, 0.5]


    def _get_vrange(self, var):
        return self.limits_undulators[var]

    @staticmethod
    def list_vars():
        return get_aircoil_list()
    

    # TODO: add losses
    @staticmethod
    def list_obses():
        return ['sases_average']

    @staticmethod
    def get_default_params():
        return {
            'waiting_time': 1,
            'interface': 'doocs',
        }

    def _get_var(self, var):
        # TODO: update pv limits every time?
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
                sa1 = self.interface.get_value("XFEL.FEL/XGM/XGM.3130.T10/INTENSITY.RAW.TRAIN")
                values.append(sa1)
                time.sleep(0.1)
            return np.mean(values)

