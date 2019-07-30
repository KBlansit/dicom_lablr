#!/usr/bin/env python

# import libraries
import os

import numpy as np
import pandas as pd

from scipy.ndimage import label

from matplotlib.patches import Rectangle

# define parameters
HOUNSFIELD_1_MIN = 130
HOUNSFIELD_2_MIN = 200
HOUNSFIELD_3_MIN = 300
HOUNSFIELD_4_MIN = 400

MIN_AGASTON_AREA = 1

CONNECTED_COMPONENTS_SHAPE = np.ones([3, 3, 3])

MICRO_CA_THRESH = 2

LINE_WIDTH = 0.5

class CalciumPatch(object):
    def __init__(self, curr_label, lbl_mtx, msk_mtx, min_ary, px_area, \
                 slice_thickness, roi_name, shape):
        """
        given a curr_label, lbl_mtx, img_mtx, min_ary get:
            - centroid of patch
            - height of patch
            - width of patch
            - volume
            - ag score
        """
        # save shape
        self.shape = shape
        self.min_ary = min_ary

        # set roi name
        self.roi_name = roi_name

        # set locations
        self.min_indx = np.stack(np.where(lbl_mtx == curr_label)).min(axis=1).round() + min_ary
        self.centroid = np.stack(np.where(lbl_mtx == curr_label)).mean(axis=1).round() + min_ary
        self.max_indx = np.stack(np.where(lbl_mtx == curr_label)).max(axis=1).round() + min_ary

        # set rectangle
        xy_loc = self.max_indx[:2][::-1]

        width = self.max_indx[1] - self.min_indx[1]
        height = self.max_indx[0] - self.min_indx[0]
        self.rect = Rectangle(xy_loc, -width, -height, 1, edgecolor="red",
                              fill = None, linewidth = LINE_WIDTH)
        self.rect.PLOTTED = False

        # set up to make measurements
        non_label_indx = np.where(lbl_mtx != curr_label)
        self.label_indx = np.where(lbl_mtx == curr_label)

        temp_msk_mtx = msk_mtx.copy()
        temp_msk_mtx[non_label_indx] = 0

        # get calcium score
        self.ca_score = get_agatston_score(temp_msk_mtx.copy(), px_area)

        # get volume
        self.ca_vol = calculate_calcium_volume(temp_msk_mtx.copy(), px_area, slice_thickness)

    def get_rectangle(self):
        """
        returns matplotlib rectangle
        """

        return self.rect

    def get_slice_range(self):
        """
        returns range of slices
        """
        return self.min_indx[-1], self.max_indx[-1]

    def set_visible(self, bool):
        """
        setter for rect
        """
        self.rect.set_visible(bool)

    def get_measurements(self):
        """
        returns ca measurements
        """
        return self.ca_score, self.ca_vol

    def get_ca_mask(self, curr_slice):
        """
        gets ca mask for curr slice
        """
        # determine slice range
        min_slice = min(self.label_indx[2]) + self.min_ary[-1]
        max_slice = max(self.label_indx[2]) + self.min_ary[-1]

        # determine if we're within range
        if min_slice <= curr_slice <= max_slice:

            # get label indx
            lbl_slc_indx = curr_slice - self.min_ary[-1]

            # get xy indx
            in_plane_indx = self.label_indx[2] == lbl_slc_indx

            # get rslt mtx of zeros to be set to one
            rslt_mtx = np.zeros(self.shape)

            # make zero mask indx
            zero_msk_indx = (
                self.label_indx[0][in_plane_indx] + self.min_ary[0],
                self.label_indx[1][in_plane_indx] + self.min_ary[1],
            )

            rslt_mtx[zero_msk_indx] = 1

        else:
            rslt_mtx = np.zeros(self.shape)

        return rslt_mtx

    def construct_message(self):
        """
        construct message
        """

        # make centroid
        info_msg = "Centroid: X: {} Y: {} Slice: {}.\n".format(
            *[int(x) for x in self.centroid][:2][::-1],
            int(self.centroid[-1]),
        )

        # get measurements
        curr_ca, curr_vol = self.get_measurements()

        # construct measurements message
        measurements_msg = "   [Ag: {}, Vol: {}].".format(
            int(round(curr_ca)),
            int(round(curr_vol)),
        )

        return info_msg + measurements_msg

    def __del__(self):
        """
        deconstructor
        """
        # remove rectanlge
        self.rect.set_visible(False)
        self.rect.remove()

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

def mask_matrix(mtx, roi_indx_lst):
    """
    INPUTS:
        mtx:
            the input matrix
        roi_indx_lst:
            the list of coordinate tuples
    OUTPUT:
        the non roi masked matrix
    """
    # make matrix to subtract off vals
    roi_mtx = np.stack(roi_indx_lst)
    min_vals = roi_mtx.min(axis=0)
    roi_mtx = roi_mtx - min_vals
    roi_mtx = np.stack([roi_mtx[:, 1], roi_mtx[:, 0], roi_mtx[:, 2]]).T

    # get all indicies of matrix
    bins = np.indices(mtx.shape)
    pos = np.stack(bins, axis=-1).reshape([-1, 3])

    # convert to list of tuples
    roi_tpl_lst = [tuple(x) for x in roi_mtx.tolist()]
    pos_tpl_lst = [tuple(x) for x in pos.tolist()]

    # get coordinates not in ROIs
    diff_set = set(pos_tpl_lst).difference(roi_tpl_lst)

    # make a matrix
    not_in_roi_mtx = np.stack(diff_set)

    # move to lists
    zero_msk_indx = not_in_roi_mtx.T.tolist()

    # mask indicies that are not in valid
    mskd_mtx = mtx.copy()
    mskd_mtx[zero_msk_indx] = 0

    # returns matrix
    return mskd_mtx

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

def get_agatston_score(mskd_mtx, px_area):
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

        # count non zero vals
        pxls = np.count_nonzero(curr_slice)

        # get area
        area = pxls * px_area

        # get max houndsfield
        mx_hu = get_max_hounsfield(curr_slice)

        # ignore if below 1 mm^2
        if area > 1 and mx_hu:

            # add to total calcium
            total_calcium = total_calcium + (area * mx_hu)

    # return
    return total_calcium

def calculate_calcium_volume(mskd_mtx, pixel_spacing, slice_thickness):
    """
    INPUT:
        mskd_mtx:
            masked matrix where values below 130 supressed
        pixel_spacing:
            the product of pixel spacing from dicom
        space_between_slices:
            the space between each slice
    OUTPUT:
        the total volume (in mm^3) of calcium
    """
    # calculate number of voxels
    num_vox = np.count_nonzero(mskd_mtx)

    # volume
    vol_vox = pixel_spacing * slice_thickness

    # calculate volume
    return num_vox * vol_vox

def get_calcifications(roi_indx_lst, dicom_lst, roi_name):
    """
    INPUTS:
        roi_indx_lst:
            the list of coordinate tuples
        dicom_lst:
            the list of dicom files
    """
    # get vals
    y_vals = [x[0] for x in roi_indx_lst]
    x_vals = [x[1] for x in roi_indx_lst]
    s_vals = [x[2] for x in roi_indx_lst]

    # get min and max
    y_rng = min(y_vals), max(y_vals) + 1
    x_rng = min(x_vals), max(x_vals) + 1
    s_rng = min(s_vals), max(s_vals) + 1

    # form matrix
    pxl_lst = [rescale_dicom(dicom_lst[x]) for x in range(*s_rng)]
    pxl_lst = [x[x_rng[0]:x_rng[1], y_rng[0]:y_rng[1]] for x in pxl_lst]
    pxl_mtx = np.stack(pxl_lst, axis=-1)

    # mask matrix
    msk_mtx = mask_matrix(pxl_mtx, roi_indx_lst)

    # mask below min houndsfield threshold
    msk_mtx[np.where(msk_mtx < HOUNSFIELD_1_MIN)] = 0

    # label image
    lbl_mtx, n_features = label(msk_mtx, CONNECTED_COMPONENTS_SHAPE)

    # get offset of array
    min_ary = np.array([x_rng[0], y_rng[0], min(s_vals)])

    # get pixel spacing
    px_area = np.prod(dicom_lst[0].PixelSpacing)

    # get space between slices
    slice_thickness = abs(float(dicom_lst[0][0x0018, 0x0050].value))

    # get centroids
    ca_lst = []
    for curr_feature in range(1, n_features + 1):

        # determine if we have enough pixels
        if lbl_mtx[np.where(lbl_mtx == curr_feature)].shape[0] < MICRO_CA_THRESH:
            continue
        # make calcium patch obj and add to list
        else:
            ca_lst.append(CalciumPatch(
                curr_feature,
                lbl_mtx,
                msk_mtx,
                min_ary,
                px_area,
                slice_thickness,
                roi_name,
                dicom_lst[0].pixel_array.shape,
            ))

    return ca_lst

def get_calcium_measurements(roi_indx_lst, dicom_lst, debug=False):
    """
    INPUTS:
        roi_indx_lst:
            the list of coordinate tuples
        dicom_lst:
            the list of dicom files
    OUTPUT:
        the calculated calcium score
    """
    # get vals
    y_vals = [x[0] for x in roi_indx_lst]
    x_vals = [x[1] for x in roi_indx_lst]
    s_vals = [x[2] for x in roi_indx_lst]

    # get min and max
    y_rng = min(y_vals), max(y_vals) + 1
    x_rng = min(x_vals), max(x_vals) + 1
    s_rng = min(s_vals), max(s_vals) + 1

    # form matrix
    pxl_lst = [rescale_dicom(dicom_lst[x]) for x in range(*s_rng)]
    pxl_lst = [x[x_rng[0]:x_rng[1], y_rng[0]:y_rng[1]] for x in pxl_lst]
    pxl_mtx = np.stack(pxl_lst, axis=-1)

    # mask matrix
    msk_mtx = mask_matrix(pxl_mtx, roi_indx_lst)

    # mask below min houndsfield threshold
    msk_mtx[np.where(msk_mtx < HOUNSFIELD_1_MIN)] = 0

    # get pixel spacing
    px_area = np.prod(dicom_lst[0].PixelSpacing)

    # get space between slices
    slice_thickness = abs(float(dicom_lst[0][0x0018, 0x0050].value))

    # get calcium score
    ca_score = get_agatston_score(msk_mtx.copy(), px_area)

    # get volume
    ca_vol = calculate_calcium_volume(msk_mtx.copy(), px_area, slice_thickness)

    return ca_score, ca_vol
