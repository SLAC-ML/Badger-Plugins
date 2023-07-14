import os
from typing import Dict, List, Optional
import time
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from badger import environment
from pydantic import Field, PositiveFloat, PositiveInt
# import matplotlib.pyplot as plt
# import matplotlib.patches as patches

env_root = os.path.dirname(os.path.realpath(__file__))
variable_info = pd.read_csv(os.path.join(env_root, 'awa_variables.csv')).set_index('NAME')
observable_info = pd.read_csv(os.path.join(env_root, 'awa_observables.csv')).set_index('NAME').T


class Environment(environment.Environment):

    name = 'awa'
    variables = {k: [v['MIN'], v['MAX']] for k, v in
                 variable_info[['MIN', 'MAX']].T.to_dict().items()}
    observables = list(observable_info.keys())

    target_charge_PV: str = 'AWAVXI11ICT:Ch1'
    target_charge: Optional[PositiveFloat] = Field(
        None, description='magnitude of target charge in nC'
    )
    fractional_charge_deviation: PositiveFloat = Field(
        0.1, description='fractional deviation from target charge allowed'
    )
    n_samples: PositiveInt = 5

    def get_observables(self, observable_names: List[str]) -> Dict:
        '''make measurements until charge range is within bounds'''

        assert self.interface, 'Must provide an interface!'

        measurements = []
        if self.target_charge is not None:
            observable_names += [self.target_charge_PV]

        # if a screen measurement is involved
        base_observable_names = [ele.split(':')[0] for ele in observable_names]
        screen_name = '13ARV1'

        # remove duplicates
        observable_names = list(set(observable_names))

        # remove names with screen name in it
        observable_names = [ele for ele in observable_names if not screen_name in ele]

        for i in range(self.n_samples):
            while True:
                if screen_name in base_observable_names:
                    measurement = self.get_screen_measurement(
                        screen_name, observable_names
                    )
                else:
                    # otherwise do normal epics communication
                    measurement = self.interface.get_values(observable_names)

                if self.target_charge is not None:
                    charge_value = measurement[self.target_charge_PV] * 1e9
                    if self.is_inside_charge_bounds(charge_value):
                        break
                    else:
                        pass
                else:
                    break
            measurements += [measurement]
            time.sleep(0.75)

        def add_suffix(series, suffix):
            vm = pd.Series([])
            for k in series.keys():
                vm[k + suffix] = series[k]
            return vm

        # create a dataframe
        df = pd.DataFrame(measurements)
        mean_results = df.mean()
        std_results = add_suffix(df.std(), '_std')

        return pd.concat([mean_results, std_results]).to_dict()

    def get_screen_measurement(self, screen_name, extra_pvs=None, visualize=False):
        extra_pvs = extra_pvs or []

        # do measurement and sort data
        observation_pvs = [
                              '13ARV1:image1:ArrayData',
                              '13ARV1:image1:ArraySize0_RBV',
                              '13ARV1:image1:ArraySize1_RBV'
                          ] + extra_pvs

        observation_pvs = list(set(observation_pvs))
        measurement = self.interface.get_values(observation_pvs)

        img = measurement.pop('13ARV1:image1:ArrayData')
        img = img.reshape(
            measurement['13ARV1:image1:ArraySize1_RBV'],
            measurement['13ARV1:image1:ArraySize0_RBV']
        )
        roi_data = np.array((350, 700, 600, 600))
        threshold = 150

        beam_data = get_beam_data(img, roi_data, threshold, visualize=visualize)
        measurement.update(
            {f'{screen_name}:{name}': beam_data[name] for name in beam_data}
        )
        return measurement

    def is_inside_charge_bounds(self, value):
        '''test to make sure that charge value is within bounds'''
        if self.target_charge is not None:
            return (
                    self.target_charge * (1.0 - self.fractional_charge_deviation)
                    <= value
                    <= self.target_charge * (1.0 + self.fractional_charge_deviation)
            )
        else:
            return True


def get_beam_data(img, roi_data, threshold, visualize=True):
    '''
        A method for processing raw screen images with a beam.

        As part of the analysis this function adds a bounding box (BB) around the beam
        distribution. The maximum BB distance from ROI cente is usable as a
        constraint, referred here as a `penalty` value. If less than zero, BB is
        entirely inside circular ROI, otherwise it is outside ROI. If the penalty
        function is positive, centroid and rms values returned are Nans.

        Returns a dict containing the following elements
            'Cx': beam centroid location in x
            'Cy': beam centroid location in y
            'Sx': rms beam size in x
            'Sy': rms beam size in y
            'penalty': penalty function value

        a region of interest (ROI) is specified as
        :                +------------------+
        :                |                  |
        :              height               |
        :                |                  |
        :               (xy)---- width -----+

        Parameters
        ----------
        img : np.ndarray
            n x m image data
        roi_data : np.ndarray
            list containing roi bounding box elements [x, y, width, height]
        threshold: int
            value to subtract from raw image, negative values after subtraction are
            set to zero
        visualize: bool, default: False
            flag to plot image and bounding box after processing

        Returns
        -------
        results : dict
            results dict
        '''

    cropped_image = img[
        roi_data[0]:roi_data[0] + roi_data[2],
        roi_data[1]:roi_data[1] + roi_data[3]
    ]

    filtered_image = gaussian_filter(cropped_image, 3.0)

    thresholded_image = np.where(
        filtered_image - threshold > 0, filtered_image - threshold, 0
    )

    total_intensity = np.sum(thresholded_image)

    cx, cy, sx, sy = calculate_stats(thresholded_image)
    c = np.array((cx, cy))
    s = np.array((sx, sy))

    # get beam region
    n_stds = 2
    pts = np.array(
        (
            c - n_stds * s,
            c + n_stds * s,
            c - n_stds * s * np.array((-1, 1)),
            c + n_stds * s * np.array((-1, 1))
        )
    )

    # get distance from beam region to ROI center
    roi_c = np.array((roi_data[2], roi_data[3])) / 2
    roi_radius = np.min((roi_c * 2, np.array(thresholded_image.shape))) / 2

    # visualization
    # if visualize:
    #     fig, ax = plt.subplots()
    #     c = ax.imshow(thresholded_image, origin='lower')
    #     ax.plot(cx, cy, '+r')
    #     fig.colorbar(c)

    #     rect = patches.Rectangle(pts[0], *s * n_stds * 2.0, facecolor='none',
    #                              edgecolor='r')
    #     ax.add_patch(rect)

    #     circle = patches.Circle(roi_c, roi_radius, facecolor='none', edgecolor='r')
    #     ax.add_patch(circle)
    #     # ax2 = ax.twinx()
    #     # ax2.plot(thresholded_image.sum(axis=0))
    #     ax.set_ylim(0, 1000)

    distances = np.linalg.norm(pts - roi_c, axis=1)

    # subtract radius to get penalty value
    bb_penalty = np.max(distances) - roi_radius
    log10_total_intensity = np.log10(total_intensity)

    results = {
        'Cx': cx,
        'Cy': cy,
        'Sx': sx,
        'Sy': sy,
        'bb_penalty': bb_penalty,
        'total_intensity': total_intensity,
        'log10_total_intensity': log10_total_intensity
    }

    if bb_penalty > 0 or log10_total_intensity < 5.5:
        for name in ['Cx', 'Cy', 'Sx', 'Sy']:
            results[name] = None

    if log10_total_intensity < 5.5:
        results['bb_penalty'] = None

    return results


def calculate_stats(img):
    rows, cols = img.shape
    row_coords = np.arange(rows)
    col_coords = np.arange(cols)

    m00 = np.sum(img)
    m10 = np.sum(col_coords[:, np.newaxis] * img.T)
    m01 = np.sum(row_coords[:, np.newaxis] * img)

    Cx = m10 / m00
    Cy = m01 / m00

    m20 = np.sum((col_coords[:, np.newaxis] - Cx) ** 2 * img.T)
    m02 = np.sum((row_coords[:, np.newaxis] - Cy) ** 2 * img)

    sx = (m20 / m00) ** 0.5
    sy = (m02 / m00) ** 0.5

    return Cx, Cy, sx, sy
