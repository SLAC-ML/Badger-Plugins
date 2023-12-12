import time
import numpy as np
from badger import environment
from badger.interface import Interface
from badger.factory import get_intf


def get_aircoil_address(magnet_name: str, number: int) -> str:
    return f'XFEL.FEL/UNDULATOR.SASE1/{magnet_name}.CELL{number}.SA1/FIELD.OFFSET'

def get_aircoil_list() -> list:
    vars_list = [] 
    for i in range(1, 37):
        if i in [9, 18]: 
            continue        # skip missing cells
        for m in ['CAX', 'CAY', 'CBX', 'CBY']:
            addr = get_aircoil_address(m, i)
            vars_list.append(addr)
    return vars_list


class Environment(environment.Environment):

    name = 'XFEL Sase1 Aircoils'

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
        return ['charge', 'sases', 'beam_energy', 'wavelength', 'ref_sase_signal', 'target_sase', 'target_disp', 'sases_average']

    @staticmethod
    def get_default_params():
        return {
            'waiting_time': 1,
            'interface': 'doocs'
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


        if obs == 'charge':
            return self.interface.get_value('XFEL.DIAG/CHARGE.ML/TORA.25.I1/CHARGE.SA1')
        elif obs == 'sases':
            try:
                sa = self.interface.get_value(
                    "XFEL.FEL/XGM/XGM.2643.T9/INTENSITY.RAW.TRAIN")
            except:
                sa = None

            time.sleep(0.1)
            print(f"return values is: {sa}")        
            return sa

        elif obs == 'sases_average':
            values = []
            for i in range(30):
                sa1 = self.interface.get_value(
                    "XFEL.FEL/XGM/XGM.2643.T9/INTENSITY.SA1.RAW.TRAIN")
                values.append(sa1)
                time.sleep(0.1)
            return np.mean(values)

        elif obs == 'beam_energy':
            try:
                tld = self.interface.get_value(
                    "XFEL.DIAG/BEAM_ENERGY_MEASUREMENT/TLD/ENERGY.DUD")
            except:
                tld = None
            #t3 = self.interface.get_value("XFEL.DIAG/BEAM_ENERGY_MEASUREMENT/T3/ENERGY.SA2")
            #t4 = self.interface.get_value("XFEL.DIAG/BEAM_ENERGY_MEASUREMENT/T4/ENERGY.SA1")
            #t5 = self.interface.get_value("XFEL.DIAG/BEAM_ENERGY_MEASUREMENT/T5/ENERGY.SA2")
            try:
                t4d = self.interface.get_value(
                    "XFEL.DIAG/BEAM_ENERGY_MEASUREMENT/T4D/ENERGY.SA1")
            except:
                t4d = None
            try:
                t5d = self.interface.get_value(
                    "XFEL.DIAG/BEAM_ENERGY_MEASUREMENT/T5D/ENERGY.SA2")          
            except:
                t5d = None
            return [tld, t4d, t5d]
        elif obs == 'wavelength':
            try:
                sa1 = self.interface.get_value(
                    "XFEL.FEL/XGM.PHOTONFLUX/XGM.2643.T9/WAVELENGTH")
            except:
                sa1 = None
            try:
                sa2 = self.interface.get_value(
                    "XFEL.FEL/XGM.PHOTONFLUX/XGM.2595.T6/WAVELENGTH")
            except:
                sa2 = None
            try:
                sa3 = self.interface.get_value(
                    "XFEL.FEL/XGM.PHOTONFLUX/XGM.3130.T10/WAVELENGTH")
            except:
                sa3 = None
            return [sa1, sa2, sa3]
        elif obs == 'ref_sase_signal':
            try:
                sa1 = self.interface.get_value(
                    "XFEL.FEL/XGM/XGM.2643.T9/INTENSITY.SA1.SLOW.TRAIN")
            except:
                sa1 = None
            try:
                sa2 = self.interface.get_value(
                    "XFEL.FEL/XGM/XGM.2595.T6/INTENSITY.SLOW.TRAIN")
            except:
                sa2 = None
            # try:
            #    sa3 = self.interface.get_value("XFEL.FEL/XGM.PHOTONFLUX/XGM.3130.T10/WAVELENGTH")
            # except:
            #    sa3 = None
            return [sa1, sa2]
        elif obs == 'target_sase':
            bpms = [
                "XFEL.DIAG/BPM/BPME.2252.SA2/X.ALL",
                "XFEL.DIAG/BPM/BPME.2258.SA2/X.ALL",
                "XFEL.DIAG/BPM/BPME.2264.SA2/X.ALL",
            ]

            orbit1 = self.read_bpms(bpms=bpms, nreadings=7)
            orbit2 = np.zeros(len(bpms))  # just [0, 0, 0, ... ]
            target = np.sqrt(np.sum((orbit2 - orbit1) ** 2))

            return target
        elif obs == "target_disp":
            bpms = ["XFEL.DIAG/BPM/BPMA.59.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMA.72.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMA.75.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMA.77.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMA.80.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMA.82.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMA.85.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMA.87.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMA.90.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMA.92.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMF.95.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMC.134.L1/X.ALL",
                    "XFEL.DIAG/BPM/BPMA.117.I1/X.ALL",
                    "XFEL.DIAG/BPM/BPMC.158.L1/X.ALL",
                    "XFEL.DIAG/BPM/BPMA.179.B1/X.ALL"]
            Vinit = self.interface.get_value("XFEL.RF/LLRF.CONTROLLER/CTRL.A1.I1/SP.AMPL")
            orbit1 = self.read_bpms(bpms=bpms, nreadings=7)

            time.sleep(0.1)
            self.interface.set_value("XFEL.RF/LLRF.CONTROLLER/CTRL.A1.I1/SP.AMPL", Vinit - 2)
            time.sleep(0.9)

            orbit2 = self.read_bpms(bpms=bpms, nreadings=7)

            self.interface.set_value("XFEL.RF/LLRF.CONTROLLER/CTRL.A1.I1/SP.AMPL", Vinit)
            time.sleep(0.9)

            target = -np.sqrt(np.sum((orbit2 - orbit1)**2))
            return target

    def read_bpms(self, bpms, nreadings):
        orbits = np.zeros((nreadings, len(bpms)))
        for i in range(nreadings):
            for j, bpm in enumerate(bpms):
                orbits[i, j] = self.interface.get_value(bpm)
            time.sleep(0.1)
        return np.mean(orbits, axis=0)

