#!/usr/bin/env python

# import libraries
import yaml

def import_anatomic_settings(path):
    """
    INPUTS:
        path:
            path to yaml file
    OUTPUT:
        list of anatomic landmarks
    """
    try:
        with open(path, "r") as f:
            data = yaml.load(f)
            return(data['anatomic_landmarks'])
    except:
        raise IOError("Cannot locate path: " + str(path))
