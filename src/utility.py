#!/usr/bin/env python

# import libraries
import re
import os
import yaml
import bisect
import shutil

import pandas as pd

try:
    import dicom
except:
    import pydicom as dicom

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
    #if re.search(".dcm$", path) is not None:
    return dicom.read_file(path, force=True)

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

def import_dicom(input_path):
    """
    INPUT:
        input_path:
            input dicom path
    OUTPUT:
        sorted dicom object
    """

    # store files and append path
    dicom_files = os.listdir(input_path)
    dicom_files = [input_path + "/" + x for x in dicom_files]

    # read dicom files
    dicom_lst = [read_dicom(x) for x in dicom_files]
    dicom_lst = [x for x in dicom_lst if x is not None]

    # sort list
    dicom_obj = sort_dicom_list(dicom_lst)

    # test that we have space between slices
    if not hasattr(dicom_lst[0], "SliceThickness"):
        raise AttributeError("Dicom seires {} does not have SliceThickness!")

    return dicom_obj

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
