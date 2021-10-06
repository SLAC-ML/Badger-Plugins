import os
import sys
import time
import numpy as np
import matlab_wrapper


class Matlab(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Matlab, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def __init__(self, *args, **kwargs):
        root = kwargs.get('root', None)
        if not root:
            root = os.getenv('MATLAB_ROOT')
        print('Starting Matlab Session')
        print('root',root)
        self.session = matlab_wrapper.MatlabSession(matlab_root=root)



class Emit_Meas():
    def __init__(self,):

        local_path = os.path.dirname(os.path.abspath(__file__))
        #base_ocelot_path = '/home/physics/adiha/optimizer_injector_2021_02_16/'
        #sys.path.append(base_ocelot_path)


        #local_path = os.path.dirname(os.path.abspath(__file__))
        self.ml = Matlab()
        self.ml.session.eval("addpath('{}')".format(local_path))

    def launch_emittance_measurment(self,):
        self.emittance_geomean = -1
        
        while (self.emittance_geomean > 2) | (self.emittance_geomean < 0.0): #what's the range of a valid emittance?
            self.ml.session.eval('clearvars')
            self.ml.session.eval('[emittance_x,emittance_y,emittance_x_std,emittance_y_std,bmag_x,bmag_y,bmag_x_std,bmag_y_std] = matlab_emittance_calc()')


            self.emittance_x = (self.ml.session.workspace.emittance_x)
            self.emittance_y = (self.ml.session.workspace.emittance_y)
            self.emittance_x_std = (self.ml.session.workspace.emittance_x_std)
            self.emittance_y_std = (self.ml.session.workspace.emittance_y_std)
            self.bmag_x = (self.ml.session.workspace.bmag_x)
            self.bmag_y = (self.ml.session.workspace.bmag_y)
            self.bmag_x_std = (self.ml.session.workspace.bmag_x_std)
            self.bmag_y_std = (self.ml.session.workspace.bmag_y_std)



            print('emittance_x',self.emittance_x,'+-',self.emittance_x_std)
            print('emittance_y',self.emittance_y,'+-',self.emittance_y_std)
            print('bmag_x',self.bmag_x,'+-',self.bmag_x_std)
            print('bmag_y',self.bmag_y,'+-',self.bmag_y_std)

            self.emittance_geomean = np.sqrt(self.emittance_x*self.emittance_y)  #gemoetric mean
            self.bmag_geomean = np.sqrt(self.bmag_x*self.bmag_y)  #gemoetric mean

            print('emittance geomean ',self.emittance_geomean )
            print('bmag geomean ',self.bmag_geomean )


            emittance_bmag = self.bmag_geomean * self.emittance_geomean
            print('emittance * bmag ',emittance_bmag )

        return self.emittance_geomean


