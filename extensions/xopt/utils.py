import numpy as np
from badger.utils import norm


def convert_evaluate(evaluate, configs):
    var_names = [next(iter(d)) for d in configs['variables']]
    vranges = np.array([d[next(iter(d))]
                        for d in configs['variables']])
    obj_names = [next(iter(d)) for d in configs['objectives']]
    rules = [d[next(iter(d))] for d in configs['objectives']]

    def _evaluate(inputs, extra_option='abc', **params):
        x = np.array([inputs[var_name] for var_name in var_names])
        X = norm(x, vranges[:, 0], vranges[:, 1]).reshape(1, -1)
        Y, _, _, _ = evaluate(X)

        outputs = {}
        for i, obj_name in enumerate(obj_names):
            rule = rules[i]
            obs = Y[0, i]
            if rule == 'MAXIMIZE':
                outputs[obj_name] = -obs
            else:
                outputs[obj_name] = obs

        return outputs

    return _evaluate
