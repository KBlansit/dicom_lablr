#!/usr/bin/env python

# import libraries
import os
import re
import yaml
import argparse
import warnings

import deepdish as dd

from pathlib import Path
from matplotlib import pyplot

# import user defined functions
from src.utility import import_dicom
from src.renderDicom import plotDicom

DASH_REGEX = re.compile(" - ")

# main
def main():
    # pass command line args
    cmd_parse = argparse.ArgumentParser(description = 'Application for scoring dicom files')
    cmd_parse.add_argument('-s', '--settings_path', help = 'path for settings file', type=str)
    cmd_parse.add_argument('-p', '--path', help = 'path for input dicom files', type=str)
    cmd_parse.add_argument('-v', '--save_path', help = 'save path for data', type=str)
    cmd_args = cmd_parse.parse_args()

    # check command line args
    if cmd_args.settings_path is None:
        raise AssertionError("No settings path specified")
    elif not os.path.exists(cmd_args.path):
        raise AssertionError("Cannot locate settings: " + cmd_args.path)

    # either requires path and user or meta data
    if cmd_args.path is not None:
        # make sure path is valid
        if not os.path.exists(cmd_args.path):
            raise AssertionError("Cannot locate path: " + cmd_args.path)

        # load parameters
        input_path = cmd_args.path

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
        input_path = data['input_path']

    # import dicom
    dicom_lst = import_dicom(input_path)

    # get uid
    p = Path(cmd_args.path)
    u_id = p.name

    # make annotation out path
    save_path = os.path.join(cmd_args.save_path, u_id + ".hd")

    # test to see if old annotation exists
    if os.path.exists(save_path):
        old_data_path = save_path
    else:
        old_data_path = None

    # plot and get data
    rslt_data = plotDicom(dicom_lst, cmd_args.settings_path, old_data_path)

    # supress warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dd.io.save(save_path, rslt_data)

if __name__ == '__main__':
    main()
