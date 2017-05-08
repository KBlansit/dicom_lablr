#!/usr/bin/env python

# import libraries
import os

# define parts of program call
base_call = 'main.py'
path_call = '-p data/ex1'
settings_call = '-s settings/settings.yaml'
user_call = '-u KevinTst'
output_call = '-o tst_output'

# make into a list
cmd_lst = [
    base_call,
    path_call,
    settings_call,
    user_call,
    output_call,
]

# source and run file
os.system(" ".join(cmd_lst))
