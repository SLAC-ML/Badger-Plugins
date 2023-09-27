import time
import numpy as np
from typing import Dict, List
from badger import environment
from badger.stats import percent_80
import logging


class Environment(environment.Environment):

    name = 'lcls'
    variables = {
        'QUAD:IN20:361:BCTRL': [],
        'QUAD:IN20:371:BCTRL': [],
        'QUAD:IN20:425:BCTRL': [],
        'QUAD:IN20:441:BCTRL': [],
        'QUAD:IN20:511:BCTRL': [],
        'QUAD:IN20:525:BCTRL': [],
        'QUAD:LI21:201:BCTRL': [],
        'QUAD:LI21:211:BCTRL': [],
        'QUAD:LI21:271:BCTRL': [],
        'QUAD:LI21:278:BCTRL': [],
        'QUAD:LI26:201:BCTRL': [],
        'QUAD:LI26:301:BCTRL': [],
        'QUAD:LI26:401:BCTRL': [],
        'QUAD:LI26:501:BCTRL': [],
        'QUAD:LI26:601:BCTRL': [],
        'QUAD:LI26:701:BCTRL': [],
        'QUAD:LI26:801:BCTRL': [],
        'QUAD:LI26:901:BCTRL': [],
        'QUAD:LTUH:620:BCTRL': [],
        'QUAD:LTUH:640:BCTRL': [],
        'QUAD:LTUH:660:BCTRL': [],
        'QUAD:LTUH:680:BCTRL': [],
        'QUAD:LTUS:620:BCTRL': [],
        'QUAD:LTUS:640:BCTRL': [],
        'QUAD:LTUS:660:BCTRL': [],
        'QUAD:LTUS:680:BCTRL': [],
        'QUAD:LI21:221:BCTRL': [],
        'QUAD:LI21:251:BCTRL': [],
        'QUAD:LI24:740:BCTRL': [],
        'QUAD:LI24:860:BCTRL': [],
        'QUAD:LTUH:440:BCTRL': [],
        'QUAD:LTUH:460:BCTRL': [],
        'SOLN:IN20:121:BCTRL': [],
        'QUAD:IN20:121:BCTRL': [],
        'QUAD:IN20:122:BCTRL': [],
        'DMD:IN20:1:DELAY_1': [],
        'DMD:IN20:1:DELAY_2': [],
        'DMD:IN20:1:WIDTH_2': [],
        'SIOC:SYS0:ML03:AO956': [],
    }
    observables = [
        'energy',
        'charge',
        'current',
        'beamrate',
        'beamsize_x',
        'beamsize_y',
        'beamsize_r',
        'beamsize_g',
        'hxr_pulse_intensity',
        'sxr_pulse_intensity',
        'pulse_id'
    ]

    # Env params
    readonly: bool = False
    points: int = 120
    losses_fname: str = None
    stats: str = 'percent_80'
    beamsize_monitor: str = '541'
    use_check_var: bool = True  # if check var reaches the target value
    trim_delay: float = 3.0  # in second

    def get_bounds(self, variable_names):
        assert self.interface, 'Must provide an interface!'

        pvs_low = [v + '.DRVL' for v in variable_names]
        pvs_high = [v + '.DRVH' for v in variable_names]
        bounds_low = self.interface.get_values(pvs_low)
        bounds_high = self.interface.get_values(pvs_high)

        bound_outputs = {}
        for i, v in enumerate(variable_names):
            bound_outputs[v] = [bounds_low[pvs_low[i]], bounds_high[pvs_high[i]]]

        return bound_outputs

    def get_variables(self, variable_names: List[str]) -> Dict:
        assert self.interface, 'Must provide an interface!'

        channel_names = []
        for v in variable_names:
            if v.endswith(':BCTRL'):
                prefix = v[:v.rfind(':')]
                readback = prefix + ':BACT'
            else:
                readback = v
            channel_names.append(readback)
        channel_outputs = self.interface.get_values(channel_names)

        variable_outputs = {v: channel_outputs[channel_names[i]]
                            for i, v in enumerate(variable_names)}

        return variable_outputs

    def set_variables(self, variable_inputs: Dict[str, float]):
        assert self.interface, 'Must provide an interface!'

        self.interface.set_values(variable_inputs)

        if not self.use_check_var:
            return

        variable_ready_flags = [v[:v.rfind(':')] + ':STATCTRLSUB.T'
                                for v in variable_inputs
                                if v.endswith(':BCTRL')]
        variable_status = self.interface.get_values(variable_ready_flags)

        timeout = 3  # second
        time_start = time.time()
        while np.any(np.array(variable_status.values())):
            time.sleep(0.1 * np.random.rand())

            variable_status = self.interface.get_values(variable_ready_flags)

            time_elapsed = time.time() - time_start
            if time_elapsed > timeout:
                break

        if self.trim_delay:
            time.sleep(self.trim_delay)  # extra time for stablizing orbits

    def get_observables(self, observable_names: List[str]) -> Dict:
        assert self.interface, 'Must provide an interface!'

        observable_outputs = {}
        mid = self.beamsize_monitor
        for obs in observable_names:
            if obs == 'energy':
                value = self.interface.get_value('BEND:DMPH:400:BDES')
            elif obs == 'charge':
                value = self.interface.get_value('SIOC:SYS0:ML00:CALC252')
            elif obs == 'current':
                value = self.interface.get_value('BLEN:LI24:886:BIMAX')
            elif obs == 'beamrate':
                value = self.interface.get_value('EVNT:SYS0:1:LCLSBEAMRATE')
            elif obs == 'beamsize_x':
                value = self.interface.get_value(f'OTRS:IN20:{mid}:XRMS')
            elif obs == 'beamsize_y':
                value = self.interface.get_value(f'OTRS:IN20:{mid}:YRMS')
            elif obs == 'beamsize_r':
                bs_x = self.interface.get_value(f'OTRS:IN20:{mid}:XRMS')
                bs_y = self.interface.get_value(f'OTRS:IN20:{mid}:YRMS')
                value = np.linalg.norm([bs_x, bs_y])
            elif obs == 'beamsize_g':
                bs_x = self.interface.get_value(f'OTRS:IN20:{mid}:XRMS')
                bs_y = self.interface.get_value(f'OTRS:IN20:{mid}:YRMS')
                value = np.sqrt(bs_x * bs_y)
            elif obs == 'hxr_pulse_intensity':
                # At lcls the repetition is 120 Hz and the readout buf size is 2800.
                # The last 120 entries correspond to pulse energies over past 1 second.
                points = self.points
                logging.info(f'Get Value of {points} points')

                try:
                    rate = self.interface.get_value('EVNT:SYS0:1:LCLSBEAMRATE')
                    logging.info(f'Beam rate: {rate}')
                    nap_time = points / (rate * 1.0)
                except Exception as e:
                    nap_time = 1
                    logging.warn(
                        'Something went wrong with the beam rate calculation. Let\'s sleep 1 second.')
                    logging.warn(f'Exception was: {e}')

                time.sleep(nap_time)

                data_raw = self.interface.get_value('GDET:FEE1:241:ENRCHSTCUHBR')
                try:
                    data = data_raw[-points:]
                    obj_tar = percent_80(data)
                    obj_mean = np.mean(data)
                    obj_stdev = np.std(data)
                except:  # if average fails use the scalar input
                    logging.warn(
                        'Detector is not a waveform PV, using scalar value')
                    obj_tar = data_raw
                    obj_mean = data_raw
                    obj_stdev = -1

                stats_dict = {
                    'percent_80': obj_tar,
                    'mean': obj_mean,
                    'stdev': obj_stdev,
                }

                value = stats_dict[self.stats]
            elif obs == 'sxr_pulse_intensity':
                # At lcls the repetition is 120 Hz and the readout buf size is 2800.
                # The last 120 entries correspond to pulse energies over past 1 second.
                points = self.points
                logging.info(f'Get Value of {points} points')

                try:
                    rate = self.interface.get_value('EVNT:SYS0:1:LCLSBEAMRATE')
                    logging.info(f'Beam rate: {rate}')
                    nap_time = points / (rate * 1.0)
                except Exception as e:
                    nap_time = 1
                    logging.warn(
                        'Something went wrong with the beam rate calculation. Let\'s sleep 1 second.')
                    logging.warn(f'Exception was: {e}')

                time.sleep(nap_time)

                data_scalar = self.interface.get_value('EM1K0:GMD:HPS:milliJoulesPerPulse')
                data_raw = self.interface.get_value('EM1K0:GMD:HPS:milliJoulesPerPulseHSTCUSBR')
                try:
                    data = data_raw[-points:]
                    obj_tar = percent_80(data)
                    obj_mean = np.mean(data)
                    obj_stdev = np.std(data)
                except:  # if average fails use the scalar input
                    logging.warn(
                        'Detector is not a waveform PV, using scalar value')
                    obj_tar = data_scalar
                    obj_mean = data_scalar
                    obj_stdev = -1

                stats_dict = {
                    'percent_80': obj_tar,
                    'mean': obj_mean,
                    'stdev': obj_stdev,
                }

                value = stats_dict[self.stats]
            elif obs == 'pulse_id':
                value = self.interface.get_value('PATT:SYS0:1:PULSEID')
            else:  # won't happen actually
                value = None

            observable_outputs[obs] = value

        return observable_outputs

    def get_system_states(self):
        assert self.interface, 'Must provide an interface!'

        ignore_small_value = lambda x: x if x > 10 else 0

        general_pvs = [
            'BEND:DMPH:400:BDES',
            'SIOC:SYS0:ML00:AO627',
            'BEND:DMPS:400:BDES',
            'SIOC:SYS0:ML00:AO628',
            # 'IOC:IN20:EV01:RG02_DESRATE',  # this one has to be treated specifically
            'SIOC:SYS0:ML00:CALC038',
            'SIOC:SYS0:ML00:CALC252',
            'BPMS:DMPH:693:TMITCUH1H',
            'BPMS:DMPS:693:TMITCUS1H',
        ]
        matching_quads = [
            'QUAD:IN20:361:BCTRL',
            'QUAD:IN20:371:BCTRL',
            'QUAD:IN20:425:BCTRL',
            'QUAD:IN20:441:BCTRL',
            'QUAD:IN20:511:BCTRL',
            'QUAD:IN20:525:BCTRL',
            'QUAD:LI21:201:BCTRL',
            'QUAD:LI21:211:BCTRL',
            'QUAD:LI21:271:BCTRL',
            'QUAD:LI21:278:BCTRL',
            'QUAD:LI26:201:BCTRL',
            'QUAD:LI26:301:BCTRL',
            'QUAD:LI26:401:BCTRL',
            'QUAD:LI26:501:BCTRL',
            'QUAD:LI26:601:BCTRL',
            'QUAD:LI26:701:BCTRL',
            'QUAD:LI26:801:BCTRL',
            'QUAD:LI26:901:BCTRL',
            'QUAD:LTUH:620:BCTRL',
            'QUAD:LTUH:640:BCTRL',
            'QUAD:LTUH:660:BCTRL',
            'QUAD:LTUH:680:BCTRL',
            'QUAD:LTUS:620:BCTRL',
            'QUAD:LTUS:640:BCTRL',
            'QUAD:LTUS:660:BCTRL',
            'QUAD:LTUS:680:BCTRL',
            'QUAD:LI21:221:BCTRL',
            'QUAD:LI21:251:BCTRL',
            'QUAD:LI24:740:BCTRL',
            'QUAD:LI24:860:BCTRL',
            'QUAD:LTUH:440:BCTRL',
            'QUAD:LTUH:460:BCTRL',
            'QUAD:IN20:121:BCTRL',
            'QUAD:IN20:122:BCTRL',
        ]

        states_general = self.interface.get_values(general_pvs)
        states_quads = self.interface.get_values(matching_quads)

        system_states = {
            'HXR electron energy [GeV]': states_general['BEND:DMPH:400:BDES'],
            'HXR photon energy [eV]': round(states_general['SIOC:SYS0:ML00:AO627']),
            'SXR electron energy [GeV]': states_general['BEND:DMPS:400:BDES'],
            'SXR photon energy [eV]': round(states_general['SIOC:SYS0:ML00:AO628']),
            'Rate [Hz]': self.interface.get_value('IOC:IN20:EV01:RG02_DESRATE', as_string=True),
            'Charge at gun [pC]': ignore_small_value(states_general['SIOC:SYS0:ML00:CALC038']),
            'Charge after BC1 [pC]': ignore_small_value(states_general['SIOC:SYS0:ML00:CALC252']),
            'Charge at HXR dump [pC]': ignore_small_value(states_general['BPMS:DMPH:693:TMITCUH1H'] * 1.602e-7),
            'Charge at SXR dump [pC]': ignore_small_value(states_general['BPMS:DMPS:693:TMITCUS1H'] * 1.602e-7),
        }
        system_states.update(states_quads)

        return system_states
