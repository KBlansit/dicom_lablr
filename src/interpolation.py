# import libraries
import numpy as np

from math import floor, ceil
from scipy.interpolate import splev, splrep

def get_1d_interpolation(x, y, t_max, times = 6, type = "linear"):
    """
    INPUT:
        x:
            x coordinates
        y:
            y coordinates
        t_max:
            range of time points to get (cine frames)
        times:
            number of periodic time frames to use for interpolation
    OUTPUT:
        perioidc inteprolation; defaults to single value if nothing
    """
    if len(set(y)) == 1:
        unique_val = y[0]
        return np.array([unique_val] * t_max)

    # potential to riase Warning
    if times < 1:
        raise AssertionError("Must have at least one interpolation period")
    elif times == 1:
        raise Warning("May not be able to interpolate with single period; may need more periods")

    # determine how many periods before and after
    pre_periods = ceil(times/2)
    after_periods = floor(times/2)

    # periodic interpolate
    x_conc = np.concatenate([x + _ for _ in (t_max * np.arange(-pre_periods, after_periods))])
    y_conc = np.concatenate([y] * times)

    # make interp x
    interp_x = np.arange(0, t_max)

    if type == "linear":
        interp_y = np.interp(interp_x, x_conc, y_conc)

    elif type == "periodic":
        # create interpolation object and interpolate
        spl = splrep(x_conc, y_conc)
        interp_y = splev(interp_x, spl)
    else:
        raise AssertionError("Type must be either linear or periodic. Got {}".format(type))


    return interp_y

def cine_interpolate(ijk_coord_arry, t_arry, t_max = 20):
    """
    INPUTS:
        ijk_coord_arry:
            numpy array of coordinates
            [indx, axis]
        t_arry:
            time point array
        t_max:
            range of time points to get (cine frames)
    OUTPUT:
        [0] interp_coords:
            idj cooridnates that have been interpolated for cine frames
        [1] interp_x:
            matching cine frames
    """

    # get interpolation
    interp_coords = [get_1d_interpolation(t_arry, x, t_max) for x in ijk_coord_arry.T]

    # get time values
    interp_x = np.arange(0, t_max)

    return interp_coords, interp_x

def linear_interpolate_slices(slice_arry, t_arry, t_max = 20, times = 6):
    """
    INPUTS:
        slice_arry:
            numpy array of slices
        t_arry:
            time point array
        t_max:
            range of time points to get (cine frames)
    OUTPUT:
        [0] interp_coords:
            slice cooridnates that have been interpolated for cine frames
        [1] interp_x:
            matching cine frames
    """

    # determine how many periods before and after
    pre_periods = ceil(times/2)
    after_periods = floor(times/2)

    # periodic interpolate
    x_conc = np.concatenate([slice_arry] * times)
    y_conc = np.concatenate([t_arry + _ for _ in (t_max * np.arange(-pre_periods, after_periods))])

    # create interpolation object and interpolate
    interp_x = np.arange(0, t_max)
    interp_y = np.round(np.interp(interp_x, y_conc, x_conc))

    return interp_y, interp_x
