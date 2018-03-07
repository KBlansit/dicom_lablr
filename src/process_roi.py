#!/usr/bin/env python

# import libraries
import os
import dicom

import numpy as np
import pandas as pd

from numpy.linalg import norm

def get_radius_indicies(roi_center, radius, dim):
    """
    INPUT:
        roi_center:
            the YX location of the circle center
        radius:
            the radius of the roi
        dim:
            tuple of the matrix shape
    OUTPUT:
        tuple of indicies that are within the radius
    """
    # get indicies for matrix calculations
    bins = np.indices(dim)
    pos = np.stack(bins, axis=-1).reshape([-1, 2])

    # determine indicies that are within radius
    distances = norm(pos - np.around(roi_center), axis=1)

    # return valid incicies
    vld_indx = pos[np.around(distances) <= radius]

    # return tuple of indicies
    return vld_indx[:, 0], vld_indx[:, 1]


def get_roi_indicies(roi_center, roi_rad, roi_bounds, roi_slice, dicom_lst):
    """
    INPUT:
        roi_center:
            the YX location of the circle center
        roi_rad:
            the radius of the roi
        roi_bounds:
            the bounds of the roi
        roi_slice:
            the slice where the roi is centered
        dicom_lst:
            the list of dicomes
    OUTPUT:
        the Y, X, Slice of the coordinates in the ROI
    """
    # get dimentions
    dicom_dim = dicom_lst[0].pixel_array.shape

    # get XY indicies
    xy_indx = get_radius_indicies(roi_center, roi_rad, dicom_dim)
    xy_indx_mtx = np.array(xy_indx).T

    # make range
    min_slice = int(max(0, roi_slice - roi_bounds))
    max_slice = int(min(roi_slice + roi_bounds, len(dicom_lst)))
    rng = range(min_slice, max_slice + 1)

    # make list of appended Y indx
    xyz_indx_lst = [np.insert(xy_indx_mtx, 2, x, axis=-1) for x in rng]

    return np.concatenate(xyz_indx_lst)
