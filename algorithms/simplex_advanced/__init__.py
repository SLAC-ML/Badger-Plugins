import os
import pickle
import numpy as np
import scipy.optimize as sopt
from operator import itemgetter
import logging


def optimize(evaluate, params):
    start_from_current, x0, scan_params_name, xtol, max_iter = \
        itemgetter('start_from_current', 'x0', 'scan_params_name', 'xtol', 'max_iter')(params)

    _, _, _, _x0 = evaluate(None)
    D = _x0.shape[1]

    if start_from_current:
        if x0:
            logging.warn("Start from the current state, x0 will be ignored")
        x0 = _x0.flatten()

    assert len(x0) == D, 'Dimension does not match!'

    # Load the dict that contains the parameters for the scan
    scan_params_filename = f'{scan_params_name}.pkl'
    algo_root = os.path.dirname(os.path.realpath(__file__))
    if scan_params_filename.startswith('/'):
        full_path = scan_params_filename
    else:
        full_path = os.path.join(algo_root, 'params', scan_params_filename)
    with open(full_path, 'rb') as f:
        scan_params = pickle.load(f, encoding='bytes')

    # Generate the initial simplex
    try:
        gp_precisionmat = scan_params[b'precision_matrix']
        gp_lengthscales = np.diag(gp_precisionmat) ** (-0.5)
    except:
        keylist = scan_params.keys()
        keylist.sort()
        gp_lengthscales = np.array([scan_params[k] for k in keylist if k[-5:] == 'Curr1'])
    gp_lengthscales *= np.sign(np.random.randn(gp_lengthscales.size))

    isim =np.zeros((len(gp_lengthscales) + 1, len(gp_lengthscales)))
    isim[0, :] = x0
    for i in range(len(x0)):
        vertex = np.zeros(len(x0))
        vertex[i] = gp_lengthscales[i] * 0.00245246 * 5 #0.05 #convert to gradient and normalize it to [0,1] <-- [-0.2,0.2]
        isim[i + 1, :] = x0 + vertex  #vertex

    logging.debug(f'ISIM = {isim}')

    def _evaluate(x):
        y, _, _, _ = evaluate(np.array(x).reshape(1, -1))
        y = y[0]

        return y

    res = sopt.fmin(_evaluate, x0, maxiter=max_iter,
                    maxfun=max_iter, xtol=xtol, ftol=1, initial_simplex=isim)

    return res
