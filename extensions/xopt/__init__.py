from badger import extension


class Extension(extension.Extension):

    name = 'xopt'

    def __init__(self):
        super().__init__()

    def list_algo(self):
        from xopt import configure

        return list(configure.KNOWN_ALGORITHMS.keys())

    def get_algo_config(self, name):
        from xopt import __version__, configure

        try:
            configs = configure.configure_algorithm({
                'name': name,
                'options': {},
            })
            return {
                'name': name,
                'version': __version__,
                'dependencies': ['xopt'],
                'function': configs['function'],
                'params': configs['options'],
            }
        except Exception as e:
            raise e
            # raise Exception(f'Algorithm {name} is not supported')

    def run(self, env, configs):
        # Lazy import to make the CLI UX faster
        from operator import itemgetter
        from badger.utils import config_list_to_dict, normalize_config_vars
        from xopt import Xopt
        from concurrent.futures import ThreadPoolExecutor as PoolExecutor
        from xopt.log import configure_logger

        routine_configs, algo_configs = itemgetter(
            'routine_configs', 'algo_configs')(configs)

        def evaluate(inputs, extra_option='abc', **params):
            env.set_vars_dict(inputs)
            outputs = env.get_obses_dict()

            return outputs

        config = {
            'xopt': {
                'output_path': None,
                'verbose': True,  # to be removed
            },
            'algorithm': {
                'name': algo_configs['name'],
                'options': algo_configs['params'],
            },
            'simulation': {
                'name': env.name,
                'evaluate': evaluate,
            },
            'vocs': {
                'name': routine_configs['name'],  # to be removed
                'description': None,  # to be removed
                'simulation': env.name,  # to be removed
                'templates': None,  # to be removed
                'variables': config_list_to_dict(normalize_config_vars(
                    routine_configs['variables'])),
                'objectives': config_list_to_dict(routine_configs['objectives']),
                'constraints': config_list_to_dict(routine_configs['constraints']),
            }
        }

        # Set up logging
        configure_logger()

        X = Xopt(config)
        executor = PoolExecutor()
        X.run(executor=executor)

        # Make the return compatible with the older versions of xopt
        try:
            return X.results
        except Exception:
            return None
