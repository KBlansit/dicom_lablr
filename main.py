#!/usr/bin/env python

# import libraries
import os
import dicom
import numpy

from matplotlib import pyplot, cm

# main
def main():
    # temp path
    tmp_path = 'data/ex1'

    # store files
    dicom_files = os.listdir(tmp_path)

    # make path
    dicom_path = tmp_path + "/" + dicom_files[5]

    # read dicom
    dc = dicom.read_file(dicom_path)

    # render

    pyplot.imshow(dc.pixel_array, cmap='gray')
    pyplot.show()




if __name__ == '__main__':
    main()
