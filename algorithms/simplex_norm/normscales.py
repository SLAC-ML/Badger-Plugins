import numpy as np
import pandas as pd
from . import parameters


def normscales_LCLS(mi, devices, default_length_scale=1., correlationsQ=False, verboseQ=True):
    # ____________________________
    # Grab device length scales

    # Load in a npy file containing hyperparameters binned for every 1 GeV of beam energy
    # get current L3 beam energy

    energy = mi.get_energy()

    pvs = [dev.eid for dev in devices]
    vals = [dev.get_value() for dev in devices]

    key = str(int(round(energy))).encode('utf-8')
    filename = parameters.path_to_hype3
    if verboseQ:
        print('Loading raw data for ', key, ' GeV from', filename)
    try:
        f = np.load(str(filename), allow_pickle=True, encoding='bytes')
    except:
        print('loading pickle...')
        with open(filename) as f_name:
            f = np.load(f_name)
    filedata0 = f[0][key]
    names0 = filedata0.keys()
    if verboseQ:
        print('\n\n\n\\', f[0])
        print(f[0][key])
        print('\n\n\n\\')
    if verboseQ:
        print(energy, names0)
    filedata = filedata0

    # scrapes
    prior_params_file = 'parameters/fit_params_2018-01_to_2018-01.pkl'
    prior_params_file_older = 'parameters/fit_params_2017-05_to_2018-01.pkl'
    if verboseQ:
        print('Building hyper params from data in file ', prior_params_file)
        print('Next, filling in gaps with ', prior_params_file_older)
        print('Next, filling in gaps with ', filename)
        print('Finally, filling in gaps with estimate from starting point and limits')
    filedata_recent = pd.read_pickle(prior_params_file)  # recent fits
    # fill in sparsely scanned quads with more data from larger time range
    filedata_older = pd.read_pickle(prior_params_file_older)
    names_recent = filedata_recent.T.keys()
    names_older = filedata_older.T.keys()
    # pvs = [pv.replace(':','_') for pv in pvs]

    # store results
    length_scales = []  # PV length scales

    # calculate the length scales
    for i, pv in enumerate(pvs):
        # note: we pull data from most recent runs, but to fill in the gaps, we can use data from a larger time window
        #       it seems like the best configs change with time so we prefer recent data

        pv_ = pv.replace(':', '_')

        # pv is in the data scrapes
        if pv_ in names_recent or pv_ in names_older:

            # use recent data unless too sparse (less than 10 points)
            if pv_ in names_recent and filedata_recent.get_value(pv_, 'number of points fitted') > 10:
                if verboseQ:
                    print('Length scales: ' + pv + ' RECENT DATA LOOKS GOOD')
                filedata = filedata_recent
            # fill in for sparse data with data from a larger time range
            elif pv_ in names_older:
                if verboseQ:
                    print('Length scales: '+pv +
                          ' DATA TOO SPARSE <= 10 ################################################')
                filedata = filedata_older
            else:
                if verboseQ:
                    print('Length scales: '+pv +
                          ' DATA TOO SPARSE <= 10 ################################################')
                filedata = filedata_recent

            # calculate hyper width
            width_m = filedata.get_value(pv_, 'width slope')
            width_b = filedata.get_value(pv_, 'width intercept')
            # width_res_m = filedata.get_value(pv, 'width residual slope')
            # width_res_b = filedata.get_value(pv, 'width residual intercept')
            pvwidth = (width_m * energy + width_b)  # prior widths
            length_scales += [pvwidth]
            if verboseQ:
                print('calculated length scale from scrapes:', pv, pvwidth)

        # data is not in the scrapes so check if in the
        elif pv in names0:
            if verboseQ:
                print('WARNING: Using length scale from ', filename)
            ave = float(filedata[pv][0])
            std = float(filedata[pv][1])
            pvwidth = std / 2.0 + 0.01
            length_scales += [pvwidth]
            if verboseQ:
                print('calculated length scale from operator list:', pv, ave, std)

        # default to estimate from limits
        else:
            try:
                if verboseQ:
                    print('WARNING: for now, default length scale is calculated in some weird legacy way. Should calculate from range and starting value.')
                ave = float(vals[i])
                std = np.sqrt(abs(ave))
                pvwidth = std / 2.0 + 0.01
                length_scales.append(pvwidth)
                if verboseQ:
                    print("calculated hyper param from Mitch's function: ", pv, ave, std, hyp)
                    print('calculated from values: ', float(vals[i]))
            except:
                if verboseQ:
                    print('WARNING: Defaulting to ', default_length_scale,
                          ' for now... (should estimate from starting value and limits in the future)')
                length_scales += [default_length_scale]

    length_scales = np.array(length_scales)

    # ____________________________
    # Grab correlations
    precision_matrix = None

    # ____________________________
    # Figure out a decent amplitude and noise scale
    try:
        # get the current mean and std of the chosen detector
        obj_func = mi.target.get_value()[:2]
        if verboseQ:
            print(('mi.points =', mi.points))
            print(('obj_func = ', obj_func))
        try:
            # SLACTarget.get_value() returns tuple with elements stat, stdev, ...
            ave = obj_func[0]
            std = obj_func[1]
        except:
            if verboseQ:
                print('Detector is not a waveform, Using scalar for hyperparameter calc')
            ave = obj_func
            # Hard code in the std when obj func is a scalar
            # Not a great way to deal with this, should probably be fixed
            std = 0.1

        if verboseQ:
            print(('INFO: amp = ', ave))

        # print('WARNING: overriding amplitude and variance hyper params')
        # ave = 1.
        # std = 0.1

        # calculating the amplitude parameter
        # start with 3 times what we see currently (stand to gain
        ave *= 3.
        if verboseQ:
            print(('INFO: amp = ', ave))
        # next, take larger of this and 2x the most we've seen in the past
        try:
            ave = np.max([ave, 2*np.max(peakFELs)])
            ave = np.max([ave, 1.5*np.max(peakFELs)])
            #ave = np.max(peakFELs)
            if verboseQ:
                print(('INFO: prior peakFELs = ', peakFELs))
            if verboseQ:
                print(('INFO: amp = ', ave))
        except:
            ave = 7.  # most mJ we've ever seen
            if verboseQ:
                print(('WARNING: using ', ave, ' mJ (most weve ever seen) for amp'))
        # next as a catch all, make the ave at least as large as 2 mJ
        ave = np.max([ave, 2.])
        if verboseQ:
            print(('INFO: amp = ', ave))
        # finally, we've never seen more than 6 mJ so keep the amp parameter less than 10 mJ
        ave = np.min([ave, 10.])
        if verboseQ:
            print(('INFO: amp = ', ave))

        # inflate a bit to account for shot noise near peak?
        std = 1.5 * std

        print('WARNNGL: mint.normascales.py - PLEASE FIX ME!!!')
        amp_variance = ave                               # signal amplitude
        single_noise_variance = std**2                      # noise variance of 1 point
        mean_noise_variance = std**2 / mi.points   # noise variance of mean of n points

    except:
        if verboseQ:
            print('WARNING: Could not grab objective since it wasn\'t passed properly to the machine interface as mi.target')
        amp_variance = 1.                                # signal amplitude
        single_noise_variance = 0.1**2                      # noise vsarince of 1 point
        # noise variance of mean of n points
        mean_noise_variance = 0.01**2

    offset = None  # constant offset for the prior mean

    return length_scales, amp_variance, single_noise_variance, mean_noise_variance, precision_matrix, None
