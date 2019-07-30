#!/usr/bin/python3

# import libraries
import os

# define parts of program call
base_call = 'main.py'
path_call = '-p data/Beehikkot/Beehikkot_2_Calcium_score'
settings_call = '-s settings/ca_settings.yaml'
output_call = '-v data/test_output'

# make into a list
cmd_lst = [
    base_call,
    path_call,
    settings_call,
    output_call,
]

command = "python3 -W ignore " + " ".join(cmd_lst)

# source and run file
os.system(command)
