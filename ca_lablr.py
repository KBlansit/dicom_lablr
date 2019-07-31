#!/usr/local/bin/python3

import matplotlib
matplotlib.use('TkAgg')

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
    cmd_parse.add_argument('-s', '--settings_path', help = 'path for settings file', type=str, default="settings/ca_settings.yaml")
    cmd_parse.add_argument('-v', '--save_path', help = 'save path for data', type=str, default="output")
    cmd_parse.add_argument('-p', '--dicom_path', help = 'path for input dicom files', type=str, default="")
    cmd_args = cmd_parse.parse_args()

    import pdb; pdb.set_trace()
    # check command line args
    settings_path = os.path.join(cmd_args.settings_path)
    if not os.path.exists(settings_path):
        raise AssertionError("Cannot locate settings: " + settings_path)

    # check dicom path check
    dicom_path = os.path.join(__file__, cmd_args.dicom_path)
    if not os.path.exists(dicom_path):
        raise AssertionError("Cannot locate dicom path: " + settings_path)

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
    dicom_lst = import_dicom(dicom_path)

    # get uid
    p = Path(dicom_path)
    u_id = p.name

    # make annotation out path
    save_path = os.path.join(__file__, cmd_args.save_path, u_id + ".hd")

    # test to see if old annotation exists
    if os.path.exists(save_path):
        old_data_path = save_path
    else:
        old_data_path = None

    # plot and get data
    rslt_data = plotDicom(dicom_lst, settings_path, old_data_path)

    # supress warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dd.io.save(save_path, rslt_data)

if __name__ == '__main__':
    main()
