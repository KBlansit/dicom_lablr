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

CURR_REL_PATH = os.path.dirname(os.path.realpath(__file__))

# main
def main():
    # pass command line args
    cmd_parse = argparse.ArgumentParser(description = 'Application for scoring dicom files')
    cmd_parse.add_argument('-s', '--settings_path', help = 'path for settings file', type=str, default="settings/ca_settings.yaml")
    cmd_parse.add_argument('-v', '--save_path', help = 'save path for data', type=str, default="output")
    cmd_parse.add_argument('-p', '--dicom_path', help = 'path for input dicom files', type=str)
    cmd_args = cmd_parse.parse_args()

    # check command line args
    settings_path = cmd_args.settings_path
    if not os.path.exists(settings_path):
        raise AssertionError("Cannot locate settings: " + settings_path)

    # check dicom path check
    dicom_path = cmd_args.dicom_path
    if not os.path.exists(dicom_path):
        raise AssertionError("Cannot locate dicom path: " + dicom_path)

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
