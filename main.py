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

    # store files and append path
    dicom_files = os.listdir(tmp_path)
    dicom_files = [tmp_path + "/" + x for x in dicom_files]

    # read dicom files
    dicom_obj = [dicom.read_file(x, force=True) for x in dicom_files]
    import pdb; pdb.set_trace()

    # render
    pyplot.imshow(dc.pixel_array, cmap='gray')
    pyplot.show()

if __name__ == '__main__':
    main()
