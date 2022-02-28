import numpy as np
from operator import itemgetter
from bayes_opt import BayesianOptimization


def optimize(evaluate, params):
    start_from_current, random_state, init_points, n_iter = itemgetter(
        'start_from_current', 'random_state', 'init_points', 'n_iter')(params)

    _, _, _, x0 = evaluate(None)
    D = x0.shape[1]

    def _evaluate(**kwargs):
        var_list = [kwargs[f'v{i}'] for i in range(D)]
        X = np.array(var_list).reshape(1, -1)
        Y, _, _, _ = evaluate(X)

        # BO assume a maximize problem
        return -Y[0, 0]

    # bounds on input params
    pbounds = {}
    for i in range(D):
        pbounds[f'v{i}'] = (0, 1)

    optimizer = BayesianOptimization(
        f=_evaluate,
        pbounds=pbounds,
        random_state=random_state,
        verbose=0,
    )

    _init_points = init_points
    if start_from_current:
        optimizer.probe(params=x0[0], lazy=True)
        _init_points -= 1

    optimizer.maximize(
        init_points=_init_points,
        n_iter=n_iter,
    )
