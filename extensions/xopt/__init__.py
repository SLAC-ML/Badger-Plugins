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

    def optimize(self, evaluate, configs):
        # Lazy import to make the CLI UX faster
        from operator import itemgetter
        from badger.utils import config_list_to_dict
        from xopt import Xopt
        from concurrent.futures import ThreadPoolExecutor as PoolExecutor
        from xopt.log import configure_logger
        from .utils import convert_evaluate

        routine_configs, algo_configs, env_configs = itemgetter(
            'routine_configs', 'algo_configs', 'env_configs')(configs)

        config = {
            'xopt': {
                'output_path': None,
            },
            'algorithm': {
                'name': algo_configs['name'],
                'options': algo_configs['params'],
            },
            'simulation': {
                'name': env_configs['name'],
                'evaluate': convert_evaluate(evaluate, routine_configs),
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
        executor = PoolExecutor()
        X.run(executor=executor)

        # This will raise an exception with older (< 0.4.3) versions of xopt
        return X.results
