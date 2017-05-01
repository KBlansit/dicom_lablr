#!/usr/bin/env python

# import libraries
import os
import dicom
import bisect
import argparse

from matplotlib import pyplot

# import user defined functions
from src.renderDicom import plotDicom

def sort_dicom_list(dicom_list):
    """
    INPUTS:
        dicom_list:
            an unsorted list of dicom objects
    OUTPUT:
        sorted list of dicom objects based off of dicom InstanceNumber
    """

    # test that all elements of the list are dicom objects
    if not all([True if type(x) == dicom.dataset.FileDataset else False for x in dicom_list]):
        raise AssertionError("Not all elements are dicom images")

    # pop first element to initialize list
    rslt_dicom_lst = [dicom_list.pop()]
    rslt_idx = [rslt_dicom_lst[0].InstanceNumber]

    # loop through list
    for element in dicom_list:
        # find index
        idx = bisect.bisect(rslt_idx, element.InstanceNumber)

        # add to lists
        rslt_dicom_lst.insert(idx, element)
        rslt_idx.insert(idx, element.InstanceNumber)

    # testing that rslt_idx is sorted (as it shoulf be!)
    if not sorted(rslt_idx) == rslt_idx:
        raise AssertionError("Did not sort correctly!")

    return rslt_dicom_lst

# main
def main():
    # pass command line args
    cmd_parse = argparse.ArgumentParser(description = 'Application for scoring dicom files')
    cmd_parse.add_argument('-p', '--path', help = 'path for input dicom files', type=str)
    cmd_parse.add_argument('-s', '--settings', help = 'path for settings file', type=str)
    cmd_args = cmd_parse.parse_args()

    # check command line args
    if cmd_args.path is None:
        raise AssertionError("No path specified")
    elif not os.path.exists(cmd_args.path):
        raise AssertionError("Cannot locate path: " + cmd_args.path)

    if cmd_args.settings is None:
        raise AssertionError("No settings path specified")
    elif not os.path.exists(cmd_args.settings):
        raise AssertionError("Cannot locate settings: " + cmd_args.path)

    # store files and append path
    dicom_files = os.listdir(cmd_args.path)
    dicom_files = [cmd_args.path + "/" + x for x in dicom_files]

    # read dicom files
    dicom_obj = [dicom.read_file(x, force=True) for x in dicom_files]

    # sort list
    dicom_obj = sort_dicom_list(dicom_obj)

    # render
    plotDicom(dicom_obj, cmd_args.settings)

if __name__ == '__main__':
    main()
