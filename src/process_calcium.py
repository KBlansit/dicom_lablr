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

def get_max_hounsfield(dicom_lst, vld_roi_indx, roi_slice, roi_bounds):
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
        the mapped peak houndsfield (1, 2, 3, 4) or None if below threshold
    """
    # get subset of dicom files
    curr_dicom_lst = subset_dicom_lst(dicom_lst, roi_slice, roi_bounds)

    # get roi matricies
    roi_mtx = np.stack([rescale_dicom(x) for x in curr_dicom_lst])

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

def get_calcium_score(roi_indicies, dicom_lst):
    """
    INPUTS:
        roi_indicies:
            the list of unique ROIs
        dicom_lst:
            the list of dicom files
    OUTPUT:
    """

    # get vals
    y_vals = [x[0] for x in roi_indicies]
    x_vals = [x[1] for x in roi_indicies]
    s_vals = [x[2] for x in roi_indicies]

    # get min and max
    y_rng = min(y_vals), max(y_vals) + 1
    x_rng = min(x_vals), max(x_vals) + 1
    s_rng = min(s_vals), max(s_vals) + 1

    # get dicomes for range in s_rng, and then crop y_rng and x_rng
    pxl_lst = [rescale_dicom(dicom_lst[x]) for x in range(*s_rng)]
    pxl_lst = [x[y_rng[0]:y_rng[1], x_rng[0]:x_rng[1]] for x in pxl_lst]

    # stack into 3D matrix
    pxl_mtx = np.stack(pxl_lst, axis=-1)

    # get all indicies of matrix
    bins = np.indices(pxl_mtx.shape)
    pos = np.stack(bins, axis=-1).reshape([-1, 3])

    # add min index
    pos[:,0] = pos[:,0] + y_rng[0]
    pos[:,1] = pos[:,1] + x_rng[0]
    pos[:,2] = pos[:,2] + s_rng[0]

    # convert to list of tuples
    tpl_lst = [tuple(x) for x in pos.tolist()]

    # get coordinates not in ROIs
    diff_set = set(tpl_lst).difference(roi_indicies)

    # make a matrix
    not_in_roi_mtx = np.stack(diff_set)
    not_in_roi_mtx[:,0] = not_in_roi_mtx[:,0] - y_rng[0]
    not_in_roi_mtx[:,1] = not_in_roi_mtx[:,1] - x_rng[0]
    not_in_roi_mtx[:,2] = not_in_roi_mtx[:,2] - s_rng[0]

    # move to lists
    zero_msk_indx = not_in_roi_mtx.T.tolist()

    # zero out pxl_mtx
    pxl_mtx[zero_msk_indx] = 0

    # blank out indicies that are not in valid
    import pdb; pdb.set_trace()












def contigous_mass_sizes(mtx):
    """
    INPUT:
        mtx:
            a 3D matrix
    OUTPUT:
        a list of sizes of contigous masses
    """
    # determine mass size
    lbl_mtx, n_features = label(mtx)
    mass_size_lst = [len(lbl_mtx[lbl_mtx == x]) for x in range(n_features)]

    # return
    return mass_size_lst

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
    px_space = np.prod(curr_dicom.PixelSpacing)

    # get area of the ROI that is above the min houndsfield threshold
    pxls = (rescale_dicom(curr_dicom)[vld_roi_indx] >= HOUNSFIELD_1_MIN).sum()

    # return area
    return px_space * pxls

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

def get_roi_score(dicom_lst, roi_center, roi_rad, roi_bounds, roi_slice):
    # HACK


    # get dimentions of dicom
    dicom_dim = dicom_lst[0].pixel_array.shape

    # get indicies
    indxs = calculate_radius_indicies(roi_center, roi_rad, dicom_dim)

    import pdb; pdb.set_trace()
