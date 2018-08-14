#!/usr/bin/env python

# import libraries
import os
import dicom

import numpy as np
import pandas as pd

def get_roi_indicies(path_indx, dicom_dims, slice_range):
    """
    INPUT:
        path_indx:
            the path indx of the roi
        dicom_dims:
            the XY shape of the input
        slice_range:
            the ranges of the roi
    OUTPUT:
        the X, Y, Slice of the coordinates in the ROI
    """

    # see if we have indicies
    if not path_indx:
        return []

    # get dimentions
    bins = np.indices(tuple(dicom_dims))
    pos = np.stack(bins, axis=-1).reshape([-1, 2])

    # get valid indicies
    vld_pos = pos[path_indx.contains_points(pos)]

    # append slice
    vld_lst = [np.insert(vld_pos, 2, x, axis=-1) for x in range(*slice_range)]

    # concatenate
    vld_indx = np.concatenate(vld_lst)

    # return
    return [tuple(x) for x in vld_indx.tolist()]
