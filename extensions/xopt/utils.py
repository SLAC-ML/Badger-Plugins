import json
import numpy as np
import pandas as pd
from badger.utils import norm, denorm
from badger.archive import load_run


def convert_evaluate(evaluate, configs):
    var_names = [next(iter(d)) for d in configs['variables']]
    vranges = np.array([d[next(iter(d))]
                        for d in configs['variables']])
    obj_names = [next(iter(d)) for d in configs['objectives']]
    rules = [d[next(iter(d))] for d in configs['objectives']]
    try:
        configs_cons = configs['constraints'] or []
    except:
        configs_cons = []
    con_names = [next(iter(d)) for d in configs_cons]
    relations = [d[next(iter(d))] for d in configs_cons]

    def _evaluate(inputs):
        x = np.array([inputs[var_name] for var_name in var_names]).reshape(1, -1)
        X = norm(x, vranges[:, 0], vranges[:, 1])
        Y, I, E, _ = evaluate(X)

        outputs = {}
        # Add objectives
        for i, obj_name in enumerate(obj_names):
            rule = rules[i]
            obs = Y[0, i]
            if rule == 'MAXIMIZE':
                outputs[obj_name] = -obs
            else:
                outputs[obj_name] = obs
        # Add constraints
        count_i = 0
        count_e = 0
        for i, con_name in enumerate(con_names):
            relation, thres = relations[i][:2]
            if relation == 'GREATER_THAN':
                outputs[con_name] = I[0, count_i] + thres
                count_i += 1
            elif relation == 'LESS_THAN':
                outputs[con_name] = thres - I[0, count_i]
                count_i += 1
            else:
                outputs[con_name] = E[0, count_e] + thres
                count_e += 1

        return outputs

    return _evaluate


def get_current_data(evaluate, configs):
    var_names = [next(iter(d)) for d in configs['variables']]
    vranges = np.array([d[next(iter(d))]
                        for d in configs['variables']])

    _, _, _, _x0 = evaluate(None)
    x0 = denorm(_x0, vranges[:, 0], vranges[:, 1])

    init_data = pd.DataFrame(x0, columns=var_names)

    return init_data


def get_init_data(configs):
    try:
        init_points = configs['init_points']
        if init_points is None:
            df = None
        else:
            df = pd.DataFrame.from_dict(init_points)

        return df
    except KeyError:
        return None


def get_run_data(filename):
    # TODO: consider data chain
    run = load_run(filename)

    init_data = pd.DataFrame(run['data'])
    init_data = init_data.drop(columns=['timestamp', 'timestamp_raw'])

    return init_data


def get_algo_params(cls):
    params = {}
    for k in cls.__fields__:
        if k in ['vocs', 'data']:
            continue

        v = cls.__fields__[k]
        try:
            _ = v.default
        except AttributeError:
            params[k] = get_algo_params(v)
            continue

        try:
            params[k] = json.loads(v.default.json())
        except AttributeError:
            params[k] = v.default

    return params
