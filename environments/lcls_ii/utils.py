import numpy as np


def get_buffer_stats(data):
    obj_tar = np.percentile(data, 80)
    obj_mean = np.mean(data)
    obj_median = np.median(data)
    obj_std = np.std(data)

    stats_dict = {
        'percent_80': obj_tar,
        'mean': obj_mean,
        'median': obj_median,
        'std': obj_std,
    }

    return stats_dict
