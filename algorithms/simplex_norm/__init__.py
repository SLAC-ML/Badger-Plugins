from asyncio.log import logger
import numpy as np
import scipy.optimize as sopt
from operator import itemgetter
import logging

from .normscales import normscales_LCLS


def calc_scales(mi, devices):
    """
    calculate scales for normalized simplex

    :return: np.array() - device_delta_limits * norm_coef
    """
    norm_scales = normscales_LCLS(mi, devices)

    if norm_scales is None:
        norm_scales = [None] * np.size(devices)

    for idx, dev in enumerate(devices):
        if norm_scales[idx] is not None:
            continue
        delta = dev.get_delta()
        norm_scales[idx] = delta
    norm_scales = np.array(norm_scales)

    # Randomize the initial steps of simplex - Talk to Joe if it fails
    # if isinstance(self.minimizer, Simplex):
    norm_scales *= np.sign(np.random.randn(norm_scales.size))
    return norm_scales


def denormalize(x, x0, norm_scales, norm_coef, scaling_coef):
    # 0.00025 is used for Simplex because of the fmin steps

    delta_x = np.array(x) * scaling_coef
    delta_x_scaled = delta_x / 0.00025 * norm_scales * norm_coef
    x = x0 + delta_x_scaled  # _x0 here should be the raw values from machine
    logger.debug(f'norm_scales = {norm_scales}')
    logger.debug(f'norm_coef = {norm_coef}')
    logger.debug(f'scaling_coef = {scaling_coef}')
    logger.debug(f'delta_x = {delta_x}')
    logger.debug(f'X Init: {x0}')
    logger.debug(f'X: {x}')

    return x


def optimize(evaluate, params):
    start_from_current, x0, isteps, norm_coef, scaling_coef, xtol, max_iter = \
        itemgetter('start_from_current', 'x0', 'isteps', 'norm_coef',
                   'scaling_coef', 'xtol', 'max_iter')(params)

    _, _, _, _x0 = evaluate(None)
    D = _x0.shape[1]

    if start_from_current:
        if x0:
            logging.warn("Start from the current state, x0 will be ignored")
        x0 = _x0.flatten()

    assert len(x0) == D, 'Dimension does not match!'

    # Calculate scales for the initial simplex
    norm_scales = calc_scales(None, None)

    if isteps is None or len(isteps) != D:
        logging.warn("Initial simplex is None")
        isim = None
    elif np.count_nonzero(isteps) != D:
        logging.warn("There is zero step. Initial simplex is None")
        isim = None
    else:
        isim = np.zeros((D + 1, D))
        isim[0] = x0
        for i in range(D):
            vertex = np.zeros(D)
            vertex[i] = isteps[i]
            isim[i + 1] = x0 + vertex

    logging.debug(f'ISIM = {isim}')

    def _evaluate(x):
        _x = denormalize(x, x0, norm_scales, norm_coef, scaling_coef)
        y, _, _, _ = evaluate(np.array(_x).reshape(1, -1))
        y = y[0]

        return y

    res = sopt.fmin(_evaluate, np.zeros_like(x0), maxiter=max_iter,
                    maxfun=max_iter, xtol=xtol, initial_simplex=isim)

    return res
