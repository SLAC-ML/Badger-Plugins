import numpy as np
from operator import itemgetter
from badger.utils import ParetoFront


def optimize(evaluate, params):
    start_from_current, max_iter = \
        itemgetter('start_from_current', 'max_iter')(params)

    _, _, _, x0 = evaluate(None)
    D = x0.shape[1]

    for i in range(max_iter):
        if start_from_current and (not i):
            x = x0
        else:
            x = np.random.rand(D).reshape(1, -1)

        y, _, _, _ = evaluate(x)

        if not i:
            pf = ParetoFront(['MINIMIZE'] * y.shape[1])

        pf.is_dominated((x, y))
    # print(len(pf.pareto_front) / max_iter)

    return pf.pareto_front, pf.pareto_set
