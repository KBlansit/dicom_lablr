#!/usr/bin/env python

# import libraries
import os
import re
import yaml
import dicom
import argparse

from matplotlib import pyplot

# import user defined functions
from src.utility import save_output, import_dicom
from src.renderDicom import plotDicom

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

    # import dicom
    dicom_obj = import_dicom(input_path)

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
