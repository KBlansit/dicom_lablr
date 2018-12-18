import os
import re
import yaml
import dicom
import shutil

import pandas as pd
import deepdish as dd

from math import floor

DICOM_REGEX = re.compile("[0-9]+")

DICOM_PATH = "X:\\cMRI FIles\\Training Data\\SAX\\dicom_files"
OLD_OUTPUT_DIR = "X:\\cMRI FIles\\Training Data\\SAX\\output_old"
NEW_OUTPUT_DIR =  "X:\\cMRI FIles\\Training Data\\SAX\\output"

f_path_lst = [os.path.join(OLD_OUTPUT_DIR, x) for x in os.listdir(OLD_OUTPUT_DIR)]
f_path_lst = [x for x in f_path_lst if os.path.exists(os.path.join(x, "meta_data.yaml"))]
f_path_lst = [x for x in f_path_lst if os.path.exists(os.path.join(x, "data.csv"))]

meta_path_lst = [os.path.join(x, "meta_data.yaml") for x in f_path_lst]
data_path_lst = [os.path.join(x, "data.csv") for x in f_path_lst]


input_path_lst = []
for i in meta_path_lst:
    with open(i) as stream:
        input_path_lst.append(yaml.load(stream)["input_path"])


i = 0

for i in range(len(f_path_lst)):

    meta_path_lst[i]

    case_path = os.path.join(*DICOM_REGEX.findall(input_path_lst[i])[-2:])
    case_path = os.path.join(DICOM_PATH, case_path, "0")

    if not os.path.exists(case_path):
        continue

    dcm_path = os.path.join(case_path, os.listdir(case_path)[0])

    unique_id = dicom.read_file(dcm_path).AccessionNumber

    curr_df = pd.read_csv(data_path_lst[i])


    curr_df




    data_dict = {


    }
