#!/usr/bin/env python

# import libraries
import os
import dicom

import numpy as np
import pandas as pd

from numpy.linalg import norm

from src.utility import import_dicom, REGEX_PARSE

# define parameters
HOUNSFIELD_1_MIN = 130
HOUNSFIELD_2_MIN = 200
HOUNSFIELD_3_MIN = 300
HOUNSFIELD_4_MIN = 400

def get_hounsfield(roi_mtx):
    """
    INPUT:
        roi_mtx:
            the roi matrix
    OUTPUT:
        the mapped peak houndsfield (1, 2, 3, 4) or None if below threshold
    """

    # get maximum value
    roi_max = roi_mtx.max()

    if roi_max < HOUNSFIELD_1_MIN:
        return None
    elif roi_max >= HOUNSFIELD_1_MIN and roi_max < HOUNSFIELD_2_MIN:
        return 1
    elif roi_max >= HOUNSFIELD_2_MIN and roi_max < HOUNSFIELD_3_MIN:
        return 2
    elif roi_max >= HOUNSFIELD_3_MIN and roi_max < HOUNSFIELD_4_MIN:
        return 3
    elif roi_max <= HOUNSFIELD_4_MIN:
        return 4

def calculate_slice_area(curr_dicom, vld_roi_indx):
    """
    INPUT:
        curr_dicom:
            the current dicom object
        vld_roi_indx:
            the valid indicies for the ROI
    OUTPUT:
        the area (in mm) for the roi that meets minimum houndsfield threshold
    """
    # get size of pixels
    px_space = np.prod(curr_dicom.pixel_spacing)

    # get area of the ROI that is above the min houndsfield threshold
    pxls = (curr_dicom.pixel_array[vld_roi_indx] >= HOUNSFIELD_1_MIN).sum()

    # return area
    return px_space * pxls

def subset_dicom_lst(dicom_lst, curr_slice, bounds):
    """
    INPUT:
        dicom_lst:
            list of dicom objects
        curr_slice:
            the central slice
        bounds:
            the extend of the slices
    OUTPUT:
        subsetted list of dicom objects
    """
    # TODO: verify indicies work
    # calculate min and max of ranges
    lower_lim = max(curr_slice - bounds - 1, 0)
    upper_lim = min(curr_slice + bounds, len(dicom_lst) - 1)

    # return
    return dicom_lst[lower_lim: upper_lim]

def determine_radius(roi_center, dim):
    """
    INPUT:
        roi_center:
            the YX location of the circle center
        dim:
            tuple of the matrix shape
    OUTPUT:
        indicies that are within the radius
    """
    # get indicies for matrix calculations
    bins = np.indices(dicom_lst[0].cols, dicom_lst[0].rows)
    pos = np.stack(bins, axis=-1).reshape([-1, 2])

    # determine indicies that are within radius
    distances = norm(pos - roi_center, axis=1)

    # return valid incicies
    return pos[np.around(distances) <= curr_roi.roi_xy_rad]

def calculate_calcium(dicom_lst, roi_bounds, roi_center, roi_slice, roi_radius):
    """
    INPUT:
        dicom_lst:
            list of dicom files
        roi_bounds:
            the roi boundary
        roi_center:
            the xy location for the center of the circle
        roi_slice:
            the slice that the roi center is placed
        roi_radius:
            the radius for the roi circle
    OUTPUT:
        tuple:
            [0]: total calcium volume
            [1]: the calculated calcium score
    """
    # get subset of dicom files
    curr_dicom_lst = subset_dicom_lst(dicom_lst, roi_bounds)

    # get indicies
    vld_roi_indx = determine_radius(roi_center, dicom_lst.pixel_array.shape)

    # get roi matricies
    roi_mtx_lst = [x.pixel_array[vld_roi_indx] for x in curr_dicom_lst]

    # get max attenuation scaler
    hounsfield_scaler = get_hounsfield(np.stack(roi_mtx_lst))

    # get area of slices above HOUNSFIELD_1_MIN
    total_area = np.array([calculate_slice_area(x) for x in curr_dicom_lst])

    # get volume
    total_volume = np.stack(total_area, axis=1) * curr_dicom_lst[0].slice_spacing

    # return total multiplied by scaler
    return [total_volume, total_volume * hounsfield_scaler]
