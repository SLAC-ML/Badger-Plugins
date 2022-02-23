import numpy as np
import os
import time
from operator import itemgetter
from .modules.bayes_optimization import BayesOpt
from .modules.OnlineGP import OGP


def optimize(evaluate, params):
    scan_params_name, n_iter = itemgetter(
        'scan_params_name', 'n_iter')(params)

    scan_params_filename = f'{scan_params_name}.npy'

    # Load the dict that contains the parameters for the scan (control pv list, starting settings, and gp hyperparams)
    algo_root = os.path.dirname(os.path.realpath(__file__))
    if scan_params_filename.startswith('/'):
        full_path = scan_params_filename
    else:
        full_path = os.path.join(algo_root, 'params', scan_params_filename)
    scan_params = np.load(full_path, allow_pickle=True).item()

    # How long to wait between acquisitions
    acquisition_delay = scan_params['acquisition_delay']

    # Create the machine interface
    start_point = scan_params['start_point'] # if start_point is set to None, the optimizer will start from the current device settings.

    if start_point is None:
        _, _, _, _x0 = evaluate(None)
        start_point = _x0.flatten()

    # Create the GP
    ndim = len(start_point)
    gp_precisionmat = scan_params['gp_precisionmat']
    gp_amp = scan_params['gp_amp']
    gp_noise = scan_params['gp_noise']
    hyps = [gp_precisionmat, np.log(gp_amp), np.log(gp_noise)]  # format the hyperparams for the OGP
    gp = OGP(ndim, hyps)

    # Create the bayesian optimizer that will use the gp as the model to optimize the machine
    opt = BayesOpt(gp, evaluate, acq_func='UCB', start_dev_vals=start_point)
    opt.ucb_params = scan_params['ucb_params']  # set the acquisition function parameters

    # Running BO
    for i in range(n_iter):
        # print('iteration =', i)
        opt.OptIter()
        time.sleep(acquisition_delay)
