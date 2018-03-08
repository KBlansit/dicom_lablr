#!/usr/bin/env python

# import libraries
import os

# define parts of program call
base_call = 'main.py'
path_call = '-p data/99752834'
settings_call = '-s settings/ex_settings.yaml'
user_call = '-u KevinTst'

# make into a list
cmd_lst = [
    base_call,
    path_call,
    settings_call,
    user_call,
]

# source and run file
os.system("python " + " ".join(cmd_lst))
