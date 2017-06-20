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
        raise IOError("Problem loading: " + str(path))

def save_output(input_path, case_id, out_data, click_df, cmd_args):
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
    #if

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
