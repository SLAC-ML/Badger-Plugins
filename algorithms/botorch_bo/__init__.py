import numpy as np
from operator import itemgetter
import torch
import botorch
import gpytorch
import logging


def optimize(evaluate, params):
    start_from_current, num_init, num_iter, beta, obj_bound = itemgetter(
        'start_from_current', 'num_init', 'num_iter', 'beta', 'obj_bound')(params)

    _, _, _, x0 = evaluate(None)
    num_controls = x0.shape[1]

    # Set min and max bounds in scaled units (0 to 1)
    bounds = torch.zeros((2, num_controls))
    bounds[1] = 1

    # Get initial values within range to sample
    initial_pts = torch.zeros((num_init, num_controls))
    for i in range(num_controls):
        initial_pts[:, i] = torch.as_tensor(
            np.random.uniform(bounds[0, i], bounds[1, i], (num_init,)))
    if start_from_current:
        initial_pts[0] = torch.as_tensor(x0[0])

    train_X = torch.as_tensor(initial_pts)  # .type(torch.DoubleTensor)
    train_Y, _, _, _ = evaluate(train_X.numpy())
    train_Y = norm(train_Y, obj_bound[0], obj_bound[1])
    train_Y = torch.as_tensor(train_Y)

    for i in range(num_iter - num_init):
        x_new, _ = get_BO_point(train_X, train_Y, bounds, beta=beta)

        # to machine x_new
        y_new, _, _, _ = evaluate(x_new.numpy())
        y_new = norm(y_new, obj_bound[0], obj_bound[1])
        y_new = torch.as_tensor(y_new)

        logging.debug(y_new)

        train_X = torch.cat((train_X, x_new), 0)
        train_Y = torch.cat((train_Y, y_new), 0)


def norm(x, lb, ub):
    return (x - lb) / (ub - lb)


def get_BO_point(x, f, bounds, precision=None, beta=1.0):
    '''

    function that trains a GP model of data and returns the next observation point using UCB
    D is input space dimensionality
    N is number of samples

    :param x: input points data, torch.tensor, shape (N,D)
    :param f: output point data, torch.tensor, shape (N,1)
    :param bounds: input space bounds, torch.tensor, shape (2,D)
    :param precision: precision matrix used for RBF kernel (must be PSD), torch.tensor, (D,D)
    :param beta: UCB optimization parameter, float
    :return x_candidate, model: next observation point and gp model w/observations
    '''

    # define GP model
    gp = botorch.models.SingleTaskGP(x.double(), f.double())  # , precision)
    mll = gpytorch.mlls.ExactMarginalLogLikelihood(gp.likelihood, gp)

    for name, item in gp.named_parameters():
        logging.debug(f'{name}:{item}')

    # fit GP hyperparameters
    logging.debug('training hyperparameters')
    botorch.fit.fit_gpytorch_model(mll)

    # do UCB acquisition
    logging.debug('optimizing acquisition function')
    UCB = botorch.acquisition.UpperConfidenceBound(gp, beta=beta, maximize=False)

    candidate, _ = botorch.optim.optimize_acqf(
        UCB, bounds=bounds, q=1, num_restarts=10, raw_samples=20)

    return candidate, gp
