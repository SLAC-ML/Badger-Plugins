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
        return ['energy', 'charge', 'current', 'beamrate', 'sase']

    @staticmethod
    def get_default_params():
        return {
            'readonly': False,
            'points': 120,
            'losses_fname': None,
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
        if not var.endswith(':BCTRL'):
            return

        prefix = var[:var.rfind(':')]
        flag = prefix + ':STATCTRLSUB.T'
        while True:
            if not self.interface.get_value(flag):
                break
            time.sleep(0.1)

    def _get_obs(self, obs):
        if obs == 'energy':
            return self.interface.get_value('BEND:DMPH:400:BDES')
        elif obs == 'charge':
            return self.interface.get_value('SIOC:SYS0:ML00:CALC252')
        elif obs == 'current':
            return self.interface.get_value('BLEN:LI24:886:BIMAX')
        elif obs == 'beamrate':
            return self.interface.get_value('EVNT:SYS0:1:LCLSBEAMRATE')
        elif obs == 'sase':
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

            data_raw = self.interface.get_value('GDET:FEE1:241:ENRCHSTBR')
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

            return [obj_tar, obj_mean, obj_stdev]

    def update_pv_limits(self, eid):
        pv_low = eid + '.DRVL'
        pv_high = eid + '.DRVH'
        low = self.interface.get_value(pv_low)
        high = self.interface.get_value(pv_high)
        self.pv_limits[eid] = (low, high)

    def update_pvs_limits(self):
        for eid in self.list_vars():
            self.update_pv_limits(eid)
