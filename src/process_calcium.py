#!/usr/bin/env python

# import libraries
import os
import dicom

import numpy as np
import pandas as pd

from scipy.ndimage import label

# define parameters
HOUNSFIELD_1_MIN = 130
HOUNSFIELD_2_MIN = 200
HOUNSFIELD_3_MIN = 300
HOUNSFIELD_4_MIN = 400

MIN_AGASTON_AREA = 1

def rescale_dicom(curr_dicom):
    """
    INPUT:
        curr_dicom
    OUTPUT:
        the transformed pixel array to a HU scale
    """
    # get image
    img = curr_dicom.pixel_array

    # get intercept and slop
    intercept = curr_dicom.RescaleIntercept
    slope = curr_dicom.RescaleSlope

    # apply transform
    img = (slope * img) + intercept

    # return
    return img

def get_max_hounsfield(roi_mtx):
    """
    INPUT:
        roi_mtx:
            the masked out non-ROI matrix
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
    elif roi_max >= HOUNSFIELD_4_MIN:
        return 4

def get_agatston_score(mskd_mtx, pixel_spacing):
    """
    INPUTS:
        mskd_mtx:
            masked matrix where values below 130 supressed
        pixel_spacing:
            the product of pixel spacing from dicom
    OUTPUT:
        the calculated total calcium
    """

    # initialize total_calcium
    total_calcium = 0

    # get calcium score
    for curr_slice_indx in range(mskd_mtx.shape[-1]):
        # get current slice
        curr_slice = mskd_mtx[:, :, curr_slice_indx]

        # get connected components for the slice
        lbl_mtx, n_features = label(curr_slice)

        # for each connected component
        for curr_feature in range(1, n_features + 1):
            # get number of pixels
            pxls = np.sum(lbl_mtx == curr_feature)

            # get area
            area = pxls * pixel_spacing

            # ignore if below 1 mm^2
            if area > 1:
                # get indicies of curr feature
                lbl_indx = np.where(lbl_mtx == curr_feature)

                # get max houndsfield
                mx_hu = get_max_hounsfield(mskd_mtx[lbl_indx])

                # add to total calcium
                total_calcium = total_calcium + (area * mx_hu)

    # return
    return total_calcium

def get_calcium_score(vld_indx, slice_range, dicom_lst):
    """
    INPUTS:
        roi_indicies:
            the list of unique ROIs
        dicom_lst:
            the list of dicom files
    OUTPUT:
    """

    # get min and max vals
    min_y, min_x = vld_indx.min(axis=0)
    max_y, max_x = vld_indx.max(axis=0)

    # get dicomes for range in s_rng, and then crop y_rng and x_rng
    pxl_lst = [rescale_dicom(dicom_lst[x]) for x in range(slice_range[0], slice_range[1] + 1)]
    pxl_lst = [x[min_x:max_x, min_y:max_y] for x in pxl_lst]

    # stack into 3D matrix
    pxl_mtx = np.stack(pxl_lst, axis=-1)

    # mask below min houndsfield threshold
    pxl_mtx[np.where(pxl_mtx < HOUNSFIELD_1_MIN)] = 0

    # get pixel spacing
    px_spacing = np.prod(dicom_lst[0].PixelSpacing)

    # get calcium score
    ca_score = get_agatston_score(pxl_mtx.copy(), px_spacing)

    print(ca_score)

def calculate_calcium_volume(dicom_lst, vld_roi_indx, roi_slice, roi_bounds):
    """
    INPUT:
        dicom_lst:
            the list of dicom objects
        vld_roi_indx:
            the valid indicies for the ROI
        roi_slice:
            the slice that the roi is centered upon
        roi_bounds:
            the extend of the slices within the roi
    OUTPUT:
        the total volume (in mm^3) of calcium
    """
    # get subset of dicom files
    curr_dicom_lst = subset_dicom_lst(dicom_lst, roi_slice, roi_bounds)

    # get area of slices above HOUNSFIELD_1_MIN
    total_area = np.array([calculate_slice_area(x, vld_roi_indx) for x in curr_dicom_lst])

    # get volume
    total_volume = total_area.sum() * curr_dicom_lst[0].SliceThickness
    import pdb; pdb.set_trace()
