#!/usr/bin/env python

# import libraries
import os
import dicom
import argparse

# import user defined functions
from src.renderDicom import plotDicom as plotDicom

def sort_dicom_list(dicom_list):
    """
    INPUTS:
        dicom_list: an unsorted list of dicom objects
    OUTPUT:
        sorted list of dicom objects based off of dicom InstanceNumber
    """

    # test that all elements of the list are dicom objects
    if not all([True if type(x) == dicom.dataset.FileDataset else False for x in dicom_obj] == False):
        raise AssertionError("Not all elements are dicom images")





# main
def main():
    # pass command line args
    cmd_parse = argparse.ArgumentParser(description = 'Application for scoring dicom files')
    cmd_parse.add_argument('-p', '--path', help = 'path for input dicom files', type=str)
    cmd_args = cmd_parse.parse_args()

    # check command line args
    if cmd_args.path is None:
        raise AssertionError("No path specified")
    elif not os.path.exists(cmd_args.path):
        raise AssertionError("Cannot locate path: " + cmd_args.path)

    # store files and append path
    dicom_files = os.listdir(cmd_args.path)
    dicom_files = [cmd_args.path + "/" + x for x in dicom_files]

    # read dicom files
    dicom_obj = [dicom.read_file(x, force=True) for x in dicom_files]
    import pdb; pdb.set_trace()
    dc = dicom_obj[6]

    # render
    plotDicom(dc)

if __name__ == '__main__':
    main()
