#!/usr/bin/env python

# import libraries
import os
import dicom

import numpy as np
import pandas as pd

from numpy.linalg import norm
from scipy.ndimage import label

from src.utility import import_dicom, REGEX_PARSE

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

def get_roi_score(dicom_lst, roi_center, roi_rad, roi_bounds, roi_slice):
    # HACK


    # get dimentions of dicom
    dicom_dim = dicom_lst[0].pixel_array.shape

    # get indicies
    indxs = calculate_radius_indicies(roi_center, roi_rad, dicom_dim)

    import pdb; pdb.set_trace()
