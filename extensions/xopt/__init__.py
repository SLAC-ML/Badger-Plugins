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

        try:
            from xopt.generators import generator_default_options

            params = generator_default_options[name].dict()
        except ImportError:  # Xopt v2.0+
            from .utils import get_algo_params
            from xopt.generators import get_generator

            params = get_algo_params(get_generator(name))

        try:
            _ = params['start_from_current']
        except KeyError:
            params['start_from_current'] = True
        try:  # remove custom GP kernel to avoid yaml parsing error for now
            del params['model']['function']
        except KeyError:
            pass
        except TypeError:
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
        import copy
        from packaging import version
        from operator import itemgetter
        from badger.utils import config_list_to_dict
        from xopt import __version__
        from xopt import Xopt
        from xopt.log import configure_logger
        from .utils import convert_evaluate, get_init_data

        routine_configs, algo_configs = itemgetter(
            'routine_configs', 'algo_configs')(configs)
        params_algo = copy.deepcopy(algo_configs['params'])
        try:
            start_from_current = params_algo['start_from_current']
            del params_algo['start_from_current']
        except KeyError:
            start_from_current = True

        config = {
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

        xopt_version = version.parse(__version__)
        flag_v2 = (xopt_version >= version.parse('2.0')) or xopt_version.is_prerelease

        if flag_v2:
            configs['strict'] = True
        else:
            configs['xopt'] = {'strict': True}

        # Set up logging
        configure_logger(level='ERROR')

        if flag_v2:
            X = Xopt(**config)
        else:
            X = Xopt(config)
        # Check initial points setting
        # If set, run the optimization with it and ignore start_from_current
        init_data = get_init_data(routine_configs)
        if init_data is not None:
            X.evaluate_data(init_data)
            X.run()
            # This will raise an exception with older (< 0.6) versions of xopt
            return X.data

        # Evaluate the current solution if specified
        # or inject data from another run
        if isinstance(start_from_current, str):
            from .utils import get_run_data

            init_data = get_run_data(start_from_current)
            X.add_data(init_data)
        elif start_from_current:
            from .utils import get_current_data

            init_data = get_current_data(evaluate, routine_configs)
            X.evaluate_data(init_data)

        X.run()

        # This will raise an exception with older (< 0.6) versions of xopt
        return X.data
