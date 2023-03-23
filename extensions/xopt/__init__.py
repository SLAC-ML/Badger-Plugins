from badger import extension


class Extension(extension.Extension):

    name = 'xopt'

    def __init__(self):
        from packaging import version
        from xopt import __version__

        if version.parse(__version__) < version.parse('0.6'):
            raise Exception('Xopt version should be >= 0.6!')

        super().__init__()

    def list_algo(self):
        from xopt.generators import generators

        return list(generators.keys())

    def get_algo_config(self, name):
        from xopt import __version__
        from xopt.generators import generator_default_options

        params = generator_default_options[name].dict()
        try:
            _ = params['max_evaluations']
        except KeyError:
            params['max_evaluations'] = 42
        try:
            _ = params['start_from_current']
        except KeyError:
            params['start_from_current'] = True
        try:  # remove custom GP kernel to avoid yaml parsing error for now
            del params['model']['function']
        except KeyError:
            pass

        try:
            return {
                'name': name,
                'version': __version__,
                'dependencies': ['xopt'],
                'params': params,
            }
        except Exception as e:
            raise e
            # raise Exception(f'Algorithm {name} is not supported')

    def get_algo_docs(self, name):
        from xopt.generators import generators

        return generators[name].__doc__

    def optimize(self, evaluate, configs):
        # Lazy import to make the CLI UX faster
        from operator import itemgetter
        from badger.utils import config_list_to_dict
        from xopt import Xopt
        from xopt.log import configure_logger
        from .utils import convert_evaluate

        routine_configs, algo_configs = itemgetter(
            'routine_configs', 'algo_configs')(configs)
        params_algo = algo_configs['params'].copy()
        try:
            max_eval = params_algo['max_evaluations']
            del params_algo['max_evaluations']  # TODO: consider the case when
            # this property exists in original generator params
        except KeyError:
            max_eval = 42
        try:
            start_from_current = params_algo['start_from_current']
            del params_algo['start_from_current']
        except KeyError:
            start_from_current = True

        config = {
            'xopt': {
                'strict': True,
                'max_evaluations': max_eval,
            },
            'generator': {
                'name': algo_configs['name'],
                **params_algo,
            },
            'evaluator': {
                'function': convert_evaluate(evaluate, routine_configs),
            },
            'vocs': {
                'variables': config_list_to_dict(routine_configs['variables']),
                'objectives': config_list_to_dict(routine_configs['objectives']),
                'constraints': config_list_to_dict(routine_configs['constraints']),
            }
        }

        # Set up logging
        configure_logger(level='ERROR')

        X = Xopt(config)

        # Evaluate the current solution if specified
        if start_from_current:
            from .utils import get_current_data

            init_data = get_current_data(evaluate, routine_configs)
            X.evaluate_data(init_data)

        X.run()

        # This will raise an exception with older (< 0.6) versions of xopt
        return X.data
