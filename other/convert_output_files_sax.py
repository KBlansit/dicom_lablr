import os
import re
import yaml
import shutil

import pandas as pd
import deepdish as dd
import pydicom as dicom

from tqdm import tqdm
from math import floor
from pathlib import Path
from itertools import product

DICOM_REGEX = re.compile("[0-9]+")

DICOM_PATH = "X:\\cMRI FIles\\Training Data\\SAX\\dicom_files"
OLD_OUTPUT_DIR = "X:\\cMRI FIles\\Training Data\\SAX\\output_old"
NEW_OUTPUT_DIR =  "X:\\cMRI FIles\\Training Data\\SAX\\output"
SETTINGS_PATH = "settings\cardiac_mri_settings.yaml"

# get settings
with open(SETTINGS_PATH, "r") as fp:
    data = yaml.load(fp)
    point_lst = list(data["anatomic_landmarks"].values())

# construct file path list
f_path_lst = [os.path.join(OLD_OUTPUT_DIR, x) for x in os.listdir(OLD_OUTPUT_DIR)]
f_path_lst = [x for x in f_path_lst if os.path.exists(os.path.join(x, "meta_data.yaml"))]
f_path_lst = [x for x in f_path_lst if os.path.exists(os.path.join(x, "data.csv"))]

# construct meta path list
meta_path_lst = [os.path.join(x, "meta_data.yaml") for x in f_path_lst]

# construct data path list
data_path_lst = [os.path.join(x, "data.csv") for x in f_path_lst]

input_path_lst = []
for i in meta_path_lst:
    with open(i) as stream:
        input_path_lst.append(yaml.load(stream)["input_path"])

# iterate over cases
for i in tqdm(range(len(f_path_lst))):

    # construct path
    case_path = os.path.join(*DICOM_REGEX.findall(input_path_lst[i])[-2:])
    case_path = os.path.join(DICOM_PATH, case_path, "0")

    # skip if we don't have path
    if not os.path.exists(case_path):
        print(case_path)
        continue

    # construct dicom path
    dcm_path = os.path.join(case_path, os.listdir(case_path)[0])

    # read in dicom file
    curr_dcm = dicom.read_file(dcm_path)

    # read in old data
    curr_df = pd.read_csv(data_path_lst[i])

    # use individual cine frames if possible
    cine_series = int(curr_dcm.CardiacNumberOfImages)
    if cine_series:
        cine_point_lst = ["{}_{}".format(x, y) for x, y in product(*[point_lst, range(cine_series)])]
        cine_number = cine_series
    else:
        cine_point_lst = [x for x in point_lst]
        cine_number = 1

    # initialize data dict
    data_dict = {
        "slice_location": dict(zip(cine_point_lst, [None for x in cine_point_lst])),
        "point_locations": dict(zip(cine_point_lst, [None for x in cine_point_lst])),
    }

    # process landmarks
    for curr_lndmrk in point_lst:
        # pass if we get a missing landmark
        if curr_df[curr_df["location"] == curr_lndmrk].isnull().values.any():
            continue

        # get landmark infomation
        xy = tuple(curr_df[curr_df["location"] == curr_lndmrk][["x", "y"]].values[0])
        img_slice = curr_df[curr_df["location"] == curr_lndmrk]["img_slice"]

        # get slice and cine number
        slice = floor(img_slice/cine_number)

        # construct curr cine key
        if cine_series:
            cine_frame = int(img_slice % cine_number)
            curr_cine_key = "{}_{}".format(curr_lndmrk, cine_frame)
        else:
            curr_cine_key = curr_lndmrk

        # assign xy and slice
        data_dict["point_locations"][curr_cine_key] = xy
        data_dict["slice_location"][curr_cine_key] = slice

    # get a unique id
    if curr_dcm.AccessionNumber:
        p = Path(f_path_lst[i])
        u_id = "{}_{}".format(curr_dcm.AccessionNumber, p.name)
    else:
        p = Path(cmd_args.path)
        u_id = p.name

    # make annotation out path
    save_path = os.path.join(NEW_OUTPUT_DIR, u_id + ".hd")
    dd.io.save(save_path, data_dict)
