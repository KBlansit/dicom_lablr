#!/usr/bin/env python

# import libraries
import os

# define parts of program call
base_call = 'main.py'
path_call = '-p data/ex2'
settings_call = '-s settings/settings.yaml'

# make into a list
cmd_lst = [
    base_call,
    path_call,
    settings_call,
]

# source and run file
os.system("export DISPLAY=localhost:0.0")
os.system("chmod +x " + base_call)
os.system(" ".join(cmd_lst))
