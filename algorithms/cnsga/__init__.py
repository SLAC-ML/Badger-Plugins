import numpy as np
import scipy as sp
from operator import itemgetter
import logging

from xopt import Xopt
from concurrent.futures import ThreadPoolExecutor as PoolExecutor


def optimize(config):
    X = Xopt(config)
    executor = PoolExecutor()
    X.run(executor=executor)

    results = X.results
    return results
