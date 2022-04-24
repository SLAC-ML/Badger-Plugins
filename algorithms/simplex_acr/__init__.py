import numpy as np
import scipy.optimize as sopt
from operator import itemgetter
import logging


def optimize(evaluate, params):
    start_from_current, x0, lb, ub, gain, xtol, max_iter = \
        itemgetter('start_from_current', 'x0', 'lb', 'ub', 'gain', 'xtol', 'max_iter')(params)

    _, _, _, _x0 = evaluate(None)
    D = _x0.shape[1]

    if start_from_current:
        if x0:
            logging.warn("Start from the current state, x0 will be ignored")
        x0 = _x0.flatten()

    assert len(x0) == D, 'Dimension does not match!'

    # Convert (possible) list to array
    x0 = np.array(x0)
    lb = np.array(lb)
    ub = np.array(ub)

    x0_raw = lb + x0 * (ub - lb)
    mu = x0_raw - gain * np.sqrt(np.abs(x0_raw))
    sigma = np.sqrt(np.abs(mu))

    x0_n = (x0_raw - mu) / sigma  # normalized x0

    def _evaluate(x_n):
        x_n = np.array(x_n)
        x_raw = mu + sigma * x_n  # denormalization from Ocelot
        x = (x_raw - lb) / (ub - lb)  # normalization for Badger
        y, _, _, _ = evaluate(x.reshape(1, -1))
        y = y[0]

        return y

    res = sopt.fmin(_evaluate, x0_n, maxiter=max_iter, maxfun=max_iter, xtol=xtol)

    return res
