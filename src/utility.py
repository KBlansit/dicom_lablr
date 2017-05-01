#!/usr/bin/env python

# import libraries
import os
import yaml

import pandas as pd

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
            return(data['anatomic_landmarks'])
    except:
        raise IOError("Cannot locate path: " + str(path))

def save_output(user_name, case_id, out_data, path=None):
    """
    INPUT:
        user_name:
            the string user name
        case_id:
            the string case id
        out_data:
            the pandas dataframe of data
        path:
            the optional path, if none, uses default
    EFFECT:
        either creates a path or uses specified path to make output
    """
    # assert out_data is pandas dataframe
    if not isinstance(out_data, pd.DataFrame):
        raise TypeError("out data is not dataframe")

    # determines if using default path
    if path is None:
        out_path = "output"
    else:
        out_path = path

    # create directory if it doesn't exist
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    # make a save path
    save_path = user_name + " - " + case_id + ".csv"

    # save data
    out_data.to_csv(out_path + "/" + save_path, index=False)
