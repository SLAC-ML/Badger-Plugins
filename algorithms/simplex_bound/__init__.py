import numpy as np
import scipy.optimize as sopt
from operator import itemgetter
import logging


def optimize(evaluate, params):
    start_from_current, x0, bounds, ftol, xtol, adaptive, max_iter, seed = \
        itemgetter('start_from_current', 'x0', 'bounds', 'ftol',
                   'xtol', 'adaptive', 'max_iter', 'seed')(params)

    _, _, _, _x0 = evaluate(None)
    D = _x0.shape[1]

    if start_from_current:
        if x0:
            logging.warn("Start from the current state, x0 will be ignored")
        x0 = _x0.flatten()
    elif x0 is None:
        np.random.seed(seed)
        x0 = []
        for bound in bounds:
            x0.append(np.random.uniform(bound[0], bound[1]))
        x0 = np.array(x0)

    assert len(x0) == D, 'Dimension does not match!'

    def _evaluate(x):
        y, _, _, _ = evaluate(np.array(x).reshape(1, -1))
        y = y[0]

        return y

    res = sopt.minimize(_evaluate, x0,
                        method='Nelder-Mead',
                        bounds=bounds,
                        options={
                            'maxiter': max_iter,
                            'maxfev': max_iter,
                            'return_all': True,
                            'adaptive': adaptive,
                            'fatol': ftol,
                            'xatol': xtol
                        })

    return res
