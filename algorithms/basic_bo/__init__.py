import numpy as np
from operator import itemgetter
from bayes_opt import BayesianOptimization


def optimize(evaluate, params):
    dimension, random_state, init_points, n_iter = itemgetter(
        'dimension', 'random_state', 'init_points', 'n_iter')(params)

    def _evaluate(**kwargs):
        var_list = [kwargs[f'v{i}'] for i in range(dimension)]
        X = np.array(var_list).reshape(1, -1)
        Y, _, _, _ = evaluate(X)

        # BO assume a maximize problem
        return -Y[0, 0]

    # bounds on input params
    pbounds = {}
    for i in range(dimension):
        pbounds[f'v{i}'] = (0, 1)

    optimizer = BayesianOptimization(
        f=_evaluate,
        pbounds=pbounds,
        random_state=random_state,
        verbose=0,
    )

    optimizer.maximize(
        init_points=init_points,
        n_iter=n_iter,
    )
