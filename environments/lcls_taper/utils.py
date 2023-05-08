import numpy as np
from zfel import sase1d


def k_taper(k0=3.5, a=0.5, n=200, split_ix=80, powr=2):
    return (
        np.hstack(
            [np.ones(split_ix), (1 - a * np.linspace(0, 1, n - split_ix) ** powr)]
        )
        * k0
    )


def taper_output(unduK, DEFAULT_INPUT):
    """
    Input:
    unduK is an array to represent taper profile (recommend to be a shape of (200,)

    Output:
    z is the position array along the undulator
    power_z is the output power along undulator
    """

    sase_input = DEFAULT_INPUT.copy()

    sase_input["unduK"] = unduK
    sase_input["z_steps"] = unduK.shape[0]

    output = sase1d.sase(sase_input)

    z = output["z"]
    power_z = output["power_z"]

    return z, power_z
