#!/usr/bin/env python

# import libraries
import os
import dicom

import numpy as np
import pandas as pd

from numpy.linalg import norm

from src.utility import import_dicom
from src.renderDicom import REGEX_PARSE


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

def calculate_calcium(dicom_lst, curr_roi, spacing_multiplier):
    """
    INPUT:
        dicom_lst:
            list of dicom files
        curr_roi:
            the current parameters for the roi
    OUTPUT:
        the calculated
    """

    # calculate min and max of ranges
    # TODO: verify indicies work
    lower_lim = max(curr_roi.img_slice - curr_roi.roi_bounds - 1, 0)
    upper_lim = min(curr_roi.img_slice + curr_roi.roi_bounds, len(curr_roi) - 1)

    curr_dicom_lst = dicom_lst[lower_lim: upper_lim]

    # get indicies for matrix calculations
    bins = np.indices(dicom_lst[0].cols, dicom_lst[0].rows)
    pos = np.stack(bins, axis=-1).reshape([-1, 2])

    # determine indicies that are within radius
    center = np.around(curr_roi["Y", "X"].as_matrix())
    distances = norm(pos - center, axis=1)
    vld_roi_indx = pos[distances <= curr_roi.roi_xy_rad]

    roi_mtx_lst = [x[vld_roi_indx] for x in pxl_lst]

    # get max attenuation scaler
    hounsfield_scaler = get_hounsfield(np.stack(roi_mtx_lst))

    # get area of slices above HOUNSFIELD_1_MIN
    total_area = np.array([calculate_slice_area(x) for x in curr_dicom_lst])

    # get volume
    total_volume = np.stack(total_area, axis=1) * curr_dicom_lst[0].slice_spacing

    # return total multiplied by scaler
    return total_volume * hounsfield_scaler

def process_annotation(input_df, dicom_lst):
    """
    INPUT:
        input_df:
            the input anntoation df
    OUTPUT:
        a list of the ROIs
    """

    # initialize lst
    roi_lst = []

    # iterate over rows
    for index, row in input_df.iterrows():
        # do for ROIs
        if REGEX_PARSE.search(row['location']).group() in ROI_LANDMARKS:
            roi_lst.append(row)

def main():
    """
    main function
    """

    # import dicom
    dicom_lst = import_dicom(input_path)

if __name__ == '__main__':
    main()
