#!/usr/bin/env python

# import libraries
import os
import re
import yaml
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
    cmd_parse.add_argument('-s', '--settings', help = 'path for settings file', type=str)

    # path and user
    cmd_parse.add_argument('-p', '--path', help = 'path for input dicom files', type=str)
    cmd_parse.add_argument('-u', '--user', help = 'user name', type=str)

    # meta data load
    cmd_parse.add_argument('-m', '--meta', help = 'path for settings file', type=str)

    cmd_parse.add_argument('-o', '--out', help = 'user name', type=str)

    cmd_args = cmd_parse.parse_args()

    # check command line args
    if cmd_args.settings is None:
        raise AssertionError("No settings path specified")
    elif not os.path.exists(cmd_args.settings):
        raise AssertionError("Cannot locate settings: " + cmd_args.path)

    # either requires path and user or meta data
    if cmd_args.path is not None and cmd_args.user is not None:
        # make sure path is valid
        if not os.path.exists(cmd_args.path):
            raise AssertionError("Cannot locate path: " + cmd_args.path)

        # load parameters
        user = cmd_args.user
        input_path = cmd_args.path

        # set system state
        system_state = "NEW_FILE"

    # have preivous metadata and data
    elif cmd_args.meta is not None:
        # make sure path is valid
        if not os.path.exists(cmd_args.meta):
            raise AssertionError("Cannot locate metadata path: " + cmd_args.meta)

        # load meta data
        try:
            with open(cmd_args.meta + "\meta_data.yaml", "r") as f:
                data = yaml.load(f)
        except:
            raise IOError("Problem loading: " + str(cmd_args.meta))

        # load from meta data
        user = data['user']
        input_path = data['input_path']

        # set system state
        system_state = "OLD_FILE"

    elif cmd_args.user is None:
        raise AssertionError("No user specified")
    else:
        raise AssertionError("Parameter specification error")

    # store files and append path
    dicom_files = os.listdir(input_path)
    dicom_files = [input_path + "/" + x for x in dicom_files]

    # read dicom files
    dicom_lst = [read_dicom(x) for x in dicom_files]
    dicom_lst = [x for x in dicom_lst if x is not None]

    # use study ID from 1st case
    study_id = os.path.relpath(input_path)

    # sort list
    dicom_obj = sort_dicom_list(dicom_lst)

    # render and return data, then save output
    if system_state == "NEW_FILE":
        rslt_data, click_df = plotDicom(dicom_obj, cmd_args)
        save_output(input_path, study_id, rslt_data, click_df, cmd_args, False)
    elif system_state == "OLD_FILE":
        rslt_data, click_df = plotDicom(dicom_obj, cmd_args, cmd_args.meta)
        save_output(input_path, study_id, rslt_data, click_df, cmd_args, True)
    else:
        raise AssertionError("Wrong system state setting")

if __name__ == '__main__':
    main()
