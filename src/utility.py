#!/usr/bin/env python

# import libraries
import re
import os
import yaml
import bisect
import shutil
import pydicom as dicom

import pandas as pd

REGEX_PARSE = re.compile("([aA-zZ]+)")

def import_anatomic_settings(path):
    """
    INPUTS:
        path:
            path to yaml file
    OUTPUT:
        list of anatomic landmarks
    """
    try:
        with open(path, "r") as f:
            data = yaml.load(f)
            return(data)
    except:
        raise IOError("Problem loading: " + str(path))

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

def sort_dicom_list(dicom_lst):
    """
    INPUTS:
        dicom_list:
            an unsorted list of dicom objects
    OUTPUT:
        sorted list of dicom objects based off of dicom InstanceNumber
    """

    # test that all elements of the list are dicom objects
    if not all([True if type(x) == dicom.dataset.FileDataset else False for x in dicom_lst]):
        raise AssertionError("Not all elements are dicom images")

    # sort
    return sorted(dicom_lst, key=lambda dicom: dicom.InstanceNumber)

def recursive_read_dicom(curr_path):
    """
    recursively reads in dicom files from unarchived file
    """
    tmp_lst = []
    for curr_f in os.listdir(curr_path):
        tmp_path = os.path.join(curr_path, curr_f)
        if os.path.isdir(tmp_path):
            tmp_lst = tmp_lst + recursive_read_dicom(tmp_path)
        else:
            # read in dicom
            curr_dicom_f = dicom.read_file(tmp_path)

            tmp_lst.append(curr_dicom_f)

    return tmp_lst

def import_dicom(input_path):
    """
    INPUT:
        input_path:
            input dicom path
    OUTPUT:
        sorted dicom object
    """

    # read in all dicoms
    dicom_lst = recursive_read_dicom(input_path)

    # sort dicoms
    dicom_lst = sort_dicom_list(dicom_lst)

    return dicom_lst

def save_output(input_path, case_id, out_data, click_df, cmd_args, replace):
    """
    INPUT:
        user_name:
            the string user name
        case_id:
            the string case id
        out_data:
            the pandas dataframe of data
        click_df:
            the pandas dataframe of clck info
        path:
            the optional path, if none, uses default
    EFFECT:
        either creates a path or uses specified path to make output
    """
    # assert out_data is pandas dataframe
    if not isinstance(out_data, pd.DataFrame):
        raise TypeError("out data is not dataframe")

    # determines if using default path
    if cmd_args.out is None:
        out_path = "output"
    else:
        out_path = cmd_args.out

    # create output directory if it doesn't exist
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    # if not redoing old file
    if replace:
        # remove file directory
        shutil.rmtree(cmd_args.meta)

        # add outpat
        out_path = cmd_args.meta

    # do not replace file
    else:
        # add case directory
        out_path = out_path + "/" + case_id

        # if case output directory exists, make a new one
        if os.path.exists(out_path):
            # determine max iteration
            tmp_path = out_path
            i = 1
            while os.path.exists(tmp_path):
                tmp_path = out_path + " - " + str(i)
                i = i + 1

            out_path = out_path + " - " + str(i - 1)

    # create out path
    os.makedirs(out_path)

    # make output dict
    out_dict = {
        "user": cmd_args.user,
        "case": case_id,
        "input_path": input_path,
    }

    # save data
    out_data.to_csv(out_path + "/data.csv", index=False)
    click_df.to_csv(out_path + "/timestamps.csv", index=False)
    with open(out_path + "/meta_data.yaml", "w") as out_f:
        yaml.dump(out_dict, out_f)

def parse_multiplicative_str(input_string):
    """
    INPUTS:
        string to parse
    OUTPUTS:
        string with redundancies removed
    """
    return re.search("([aA-zZ]+)", input_string).group()
