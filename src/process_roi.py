#!/usr/bin/env python

# import libraries
import os
import dicom

import numpy as np
import pandas as pd

from numpy.linalg import norm

def get_roi_indicies(path_indx, dicom_dims):
    """
    INPUT:
        path_indx:
            the matplotlib Path indicies of a vertex
        shape:
            the XYZ shape of the input
    OUTPUT:
        the Y, X, Slice of the coordinates in the ROI
    """

    # get dimentions
    bins = np.indices(tuple(dicom_dims))
    pos = np.stack(bins, axis=-1).reshape([-1, 2])

    return pos[path_indx.contains_points(pos)]
