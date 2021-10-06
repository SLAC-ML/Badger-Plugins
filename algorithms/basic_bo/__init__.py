import numpy as np
from operator import itemgetter
from bayes_opt import BayesianOptimization


def optimize(evaluate, params):
    random_state, init_points, n_iter = itemgetter(
        'random_state', 'init_points', 'n_iter')(params)

    def _evaluate(varx, vary, varz):
        X = np.array([varx, vary, varz]).reshape(1, -1)
        Y = evaluate(X)

        return Y

    # bounds on input params
    pbounds = {
        'varx': (0.44, 0.55),
        'vary': (-0.02, 0.02),
        'varz': (-0.02, 0.02)
    }

    optimizer = BayesianOptimization(
        f=_evaluate,
        pbounds=pbounds,
        random_state=random_state
    )

    optimizer.maximize(
        init_points=init_points,
        n_iter=n_iter,
    )
