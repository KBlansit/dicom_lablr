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

def save_output(user_name, case_id, out_data, click_df, cmd_args):
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

    # add case directory
    out_path = out_path + "/" + case_id

    # if not redoing old file
    if

    # if case output directory exists, make a new one
    if os.path.exists(out_path):
        # determine max iteration
        tmp_path = out_path
        i = 1
        while os.path.exists(tmp_path):
            tmp_path = out_path + " - " + str(i)
            i = i + 1

        out_path = out_path + " - " + str(i - 1)

    os.makedirs(out_path)

    # make a save path
    save_path_data = user_name + " - " + case_id + " - data" + ".csv"
    save_path_timestamps = user_name + " - " + case_id + " - timestamps" + ".csv"
    input_path = "input_path" + ".txt"

    # save data
    out_data.to_csv(out_path + "/" + save_path_data, index=False)
    click_df.to_csv(out_path + "/" + save_path_timestamps, index=False)
    with open(out_path + "/" + input_path, "w") as f:
        f.write(cmd_args.path)
