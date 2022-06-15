import time
import numpy as np
from badger import environment
from badger.interface import Interface
from badger.stats import percent_80
import logging


class Environment(environment.Environment):

    name = 'lcls'

    def __init__(self, interface: Interface, params):
        super().__init__(interface, params)

        self.pv_limits = {}
        # self.update_pvs_limits()  # don't do it here, it's too heavy

    @staticmethod
    def list_vars():
        return [
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
            'SOLN:IN20:121:BCTRL',
            'QUAD:IN20:121:BCTRL',
            'QUAD:IN20:122:BCTRL',
            'DMD:IN20:1:DELAY_1',
            'DMD:IN20:1:DELAY_2',
            'DMD:IN20:1:WIDTH_2',
            'SIOC:SYS0:ML03:AO956',
        ]

    # TODO: add losses
    @staticmethod
    def list_obses():
        return [
            'energy',
            'charge',
            'current',
            'beamrate',
            'beamsize_x',
            'beamsize_y',
            'beamsize_r',
            'hxr_pulse_intensity',
            'sxr_pulse_intensity',
        ]

    @staticmethod
    def get_default_params():
        return {
            'readonly': False,
            'points': 120,
            'losses_fname': None,
            'stats': 'percent_80',
            'beamsize_monitor': '541',
            'use_check_var': True,  # if check var reaches the target value
            'trim_delay': 3,  # in second
        }

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
        if not self.params['use_check_var']:
            return 0

        if not var.endswith(':BCTRL'):
            return 0

        prefix = var[:var.rfind(':')]
        flag = prefix + ':STATCTRLSUB.T'
        return self.interface.get_value(flag)

    def vars_changed(self, vars, values):
        time.sleep(self.params['trim_delay'])  # extra time for stablizing orbits

    def _get_obs(self, obs):
        mid = self.params['beamsize_monitor']
        if obs == 'energy':
            return self.interface.get_value('BEND:DMPH:400:BDES')
        elif obs == 'charge':
            return self.interface.get_value('SIOC:SYS0:ML00:CALC252')
        elif obs == 'current':
            return self.interface.get_value('BLEN:LI24:886:BIMAX')
        elif obs == 'beamrate':
            return self.interface.get_value('EVNT:SYS0:1:LCLSBEAMRATE')
        elif obs == 'beamsize_x':
            return self.interface.get_value(f'OTRS:IN20:{mid}:XRMS')
        elif obs == 'beamsize_y':
            return self.interface.get_value(f'OTRS:IN20:{mid}:YRMS')
        elif obs == 'beamsize_r':
            bs_x = self.interface.get_value(f'OTRS:IN20:{mid}:XRMS')
            bs_y = self.interface.get_value(f'OTRS:IN20:{mid}:YRMS')
            return np.linalg.norm([bs_x, bs_y])
        elif obs == 'hxr_pulse_intensity':
            # At lcls the repetition is 120 Hz and the readout buf size is 2800.
            # The last 120 entries correspond to pulse energies over past 1 second.
            points = self.params['points']
            logging.info(f'Get Value of {points} points')

            try:
                rate = self._get_obs('beamrate')
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

            return stats_dict[self.params['stats']]
        elif obs == 'sxr_pulse_intensity':
            # At lcls the repetition is 120 Hz and the readout buf size is 2800.
            # The last 120 entries correspond to pulse energies over past 1 second.
            points = self.params['points']
            logging.info(f'Get Value of {points} points')

            try:
                rate = self._get_obs('beamrate')
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

            return stats_dict[self.params['stats']]

    def get_system_states(self):
        return {
            'HXR electron energy [GeV]': self.interface.get_value('BEND:DMPH:400:BDES'),
            'HXR photon energy [eV]': self.interface.get_value('SIOC:SYS0:ML00:AO627'),
            'SXR electron energy [GeV]': self.interface.get_value('BEND:DMPS:400:BDES'),
            'SXR photon energy [eV]': self.interface.get_value('SIOC:SYS0:ML00:AO628'),
            'Rate [Hz]': self.interface.get_value('IOC:IN20:EV01:RG02_DESRATE'),
            'Charge at gun [pC]': self.interface.get_value('SIOC:SYS0:ML00:CALC038'),
            'Charge after BC1 [pC]': self.interface.get_value('SIOC:SYS0:ML00:CALC252'),
            'Charge at HXR dump [pC]': self.interface.get_value('BPMS:DMPH:693:TMITCUH1H') * 1.602e-7,
            'Charge at SXR dump [pC]': self.interface.get_value('BPMS:DMPS:693:TMITCUS1H') * 1.602e-7,
            # All matching quads
            'QUAD:IN20:361:BCTRL': self.interface.get_value('QUAD:IN20:361:BCTRL'),
            'QUAD:IN20:371:BCTRL': self.interface.get_value('QUAD:IN20:371:BCTRL'),
            'QUAD:IN20:425:BCTRL': self.interface.get_value('QUAD:IN20:425:BCTRL'),
            'QUAD:IN20:441:BCTRL': self.interface.get_value('QUAD:IN20:441:BCTRL'),
            'QUAD:IN20:511:BCTRL': self.interface.get_value('QUAD:IN20:511:BCTRL'),
            'QUAD:IN20:525:BCTRL': self.interface.get_value('QUAD:IN20:525:BCTRL'),
            'QUAD:LI21:201:BCTRL': self.interface.get_value('QUAD:LI21:201:BCTRL'),
            'QUAD:LI21:211:BCTRL': self.interface.get_value('QUAD:LI21:211:BCTRL'),
            'QUAD:LI21:271:BCTRL': self.interface.get_value('QUAD:LI21:271:BCTRL'),
            'QUAD:LI21:278:BCTRL': self.interface.get_value('QUAD:LI21:278:BCTRL'),
            'QUAD:LI26:201:BCTRL': self.interface.get_value('QUAD:LI26:201:BCTRL'),
            'QUAD:LI26:301:BCTRL': self.interface.get_value('QUAD:LI26:301:BCTRL'),
            'QUAD:LI26:401:BCTRL': self.interface.get_value('QUAD:LI26:401:BCTRL'),
            'QUAD:LI26:501:BCTRL': self.interface.get_value('QUAD:LI26:501:BCTRL'),
            'QUAD:LI26:601:BCTRL': self.interface.get_value('QUAD:LI26:601:BCTRL'),
            'QUAD:LI26:701:BCTRL': self.interface.get_value('QUAD:LI26:701:BCTRL'),
            'QUAD:LI26:801:BCTRL': self.interface.get_value('QUAD:LI26:801:BCTRL'),
            'QUAD:LI26:901:BCTRL': self.interface.get_value('QUAD:LI26:901:BCTRL'),
            'QUAD:LTUH:620:BCTRL': self.interface.get_value('QUAD:LTUH:620:BCTRL'),
            'QUAD:LTUH:640:BCTRL': self.interface.get_value('QUAD:LTUH:640:BCTRL'),
            'QUAD:LTUH:660:BCTRL': self.interface.get_value('QUAD:LTUH:660:BCTRL'),
            'QUAD:LTUH:680:BCTRL': self.interface.get_value('QUAD:LTUH:680:BCTRL'),
            'QUAD:LTUS:620:BCTRL': self.interface.get_value('QUAD:LTUS:620:BCTRL'),
            'QUAD:LTUS:640:BCTRL': self.interface.get_value('QUAD:LTUS:640:BCTRL'),
            'QUAD:LTUS:660:BCTRL': self.interface.get_value('QUAD:LTUS:660:BCTRL'),
            'QUAD:LTUS:680:BCTRL': self.interface.get_value('QUAD:LTUS:680:BCTRL'),
            'QUAD:LI21:221:BCTRL': self.interface.get_value('QUAD:LI21:221:BCTRL'),
            'QUAD:LI21:251:BCTRL': self.interface.get_value('QUAD:LI21:251:BCTRL'),
            'QUAD:LI24:740:BCTRL': self.interface.get_value('QUAD:LI24:740:BCTRL'),
            'QUAD:LI24:860:BCTRL': self.interface.get_value('QUAD:LI24:860:BCTRL'),
            'QUAD:LTUH:440:BCTRL': self.interface.get_value('QUAD:LTUH:440:BCTRL'),
            'QUAD:LTUH:460:BCTRL': self.interface.get_value('QUAD:LTUH:460:BCTRL'),
            'QUAD:IN20:121:BCTRL': self.interface.get_value('QUAD:IN20:121:BCTRL'),
            'QUAD:IN20:122:BCTRL': self.interface.get_value('QUAD:IN20:122:BCTRL'),
        }

    def update_pv_limits(self, eid):
        pv_low = eid + '.DRVL'
        pv_high = eid + '.DRVH'
        low = self.interface.get_value(pv_low)
        high = self.interface.get_value(pv_high)
        self.pv_limits[eid] = (low, high)

    def update_pvs_limits(self):
        for eid in self.list_vars():
            self.update_pv_limits(eid)
