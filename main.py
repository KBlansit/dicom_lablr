#!/usr/bin/env python

# import libraries
import os
import re
import dicom
import bisect
import argparse

from matplotlib import pyplot

# import user defined functions
from src.utility import save_output
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

def read_dicom(path):
    """
    INPUTS:
        path:
            a string denoting the path
    OUTPUT:
        list object of dicom files
    """
    # regular expression search for .dcm file
    if re.search(".dcm$", path) is not None:
        return dicom.read_file(path, force=True)

# main
def main():
    # pass command line args
    cmd_parse = argparse.ArgumentParser(description = 'Application for scoring dicom files')
    cmd_parse.add_argument('-p', '--path', help = 'path for input dicom files', type=str)
    cmd_parse.add_argument('-s', '--settings', help = 'path for settings file', type=str)
    cmd_parse.add_argument('-u', '--user', help = 'user name', type=str)
    cmd_parse.add_argument('-o', '--out', help = 'user name', type=str)
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

    if cmd_args.user is None:
        raise AssertionError("No user specified")

    # store files and append path
    dicom_files = os.listdir(cmd_args.path)
    dicom_files = [cmd_args.path + "/" + x for x in dicom_files]

    # read dicom files
    dicom_lst = [read_dicom(x) for x in dicom_files]
    dicom_lst = [x for x in dicom_lst if x is not None]

    # use study ID from 1st case
    study_id = dicom_lst[0].StudyID

    # sort list
    dicom_obj = sort_dicom_list(dicom_lst)

    # render and return data
    rslt_data, click_df = plotDicom(dicom_obj, cmd_args)

    # save output
    save_output(cmd_args.user, study_id, rslt_data, click_df, cmd_argspath, cmd_args.out)

if __name__ == '__main__':
    main()
