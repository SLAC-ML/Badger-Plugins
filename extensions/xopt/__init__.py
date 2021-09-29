from badger import extension


class Extension(extension.Extension):

    name = 'xopt'

    def __init__(self):
        super().__init__()

    def list_algo(self):
        return ['cnsga', 'bayesian_exploration']

    def get_algo_config(self, name):
        if name == 'cnsga':
            return {
                'name': 'cnsga',
                'version': '0.1',
                'dependencies': [
                    'xopt',
                ],
                'params': {
                    'max_generations': 50,
                    'population_size': 128,
                    'crossover_probability': 0.9,
                    'mutation_probability': 1.0,
                    'selection': 'auto',
                    'verbose': True,
                    'population': None,
                }
            }
        elif name == 'bayesian_exploration':
            return {
                'name': 'bayesian_exploration',
                'version': '0.1',
                'dependencies': [
                    'xopt',
                ],
                'params': {
                    'n_initial_samples': 5,
                    'n_steps': 25,
                    'verbose': True,
                    'use_gpu': False,
                    'generator_options': {
                        'batch_size': 1,
                    }
                }
            }
        else:
            raise Exception(f'Algorithm {name} is not supported')

    def run(self, env, configs):
        # Lazy import to make the CLI UX faster
        from operator import itemgetter
        from badger.utils import config_list_to_dict, normalize_config_vars
        from xopt import Xopt
        from concurrent.futures import ThreadPoolExecutor as PoolExecutor

        routine_configs, algo_configs = itemgetter(
            'routine_configs', 'algo_configs')(configs)

        def evaluate(inputs, extra_option='abc', **params):
            env.set_vars_dict(inputs)
            outputs = env.get_obses_dict()

            return outputs

        config = {
            'xopt': {
                'output_path': None,
                'verbose': True,
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
                'name': routine_configs['name'],
                'description': None,
                'simulation': env.name,
                'templates': None,
                'variables': config_list_to_dict(normalize_config_vars(
                    routine_configs['variables'])),
                'objectives': config_list_to_dict(routine_configs['objectives']),
                'constraints': config_list_to_dict(routine_configs['constraints']),
            }
        }

        X = Xopt(config)
        executor = PoolExecutor()
        X.run(executor=executor)

        # The conda version of xopt is outdated and does not support this
        # results = X.results

        # return results
