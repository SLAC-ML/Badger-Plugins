
#environments to source:
source $TOOLS/script/ENVS64.bash
source /usr/local/lcls/package/anaconda/envs/python3.7env/bin/activate

#for using with class:
#in python
>>> from test_emit_no_ctrl_class import *
>>> em = Emit_Meas()
Starting Matlab Session
('root', '/usr/local/lcls/package/matlab/2019a')
>>> emit = em.launch_emittance_measurment()
