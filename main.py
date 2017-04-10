#!/usr/bin/env python

# import libraries
import os
import dicom
import numpy
import argparse

from matplotlib import pyplot, cm

# main
def main():
    # pass command line args
    cmd_parse = argparse.ArgumentParser(description = 'Application for scoring dicom files')
    cmd_parse.add_argument('-p', '--path', help = 'path for input dicom files', type=str)
    cmd_args = cmd_parse.parse_args()

    # check command line args
    if cmd_args.path is None:
        raise AssertionError("No path specified")
    elif not os.path.exists(cmd_args.path):
        raise AssertionError("Cannot locate path: " + cmd_args.path)

    # store files and append path
    dicom_files = os.listdir(cmd_args.path)
    dicom_files = [cmd_args.path + "/" + x for x in dicom_files]

    # read dicom files
    dicom_obj = [dicom.read_file(x, force=True) for x in dicom_files]

    dc = dicom_obj[6]

    # render####
    fig, (ax) = pyplot.subplots(1)

    # make figure
    ax = pyplot.imshow(dc.pixel_array, cmap='gray')

    def fun1(event):
        if event.key != 't':
            return
        print(22)

    pyplot.connect('key_press_event', fun1)

    pyplot.show()

if __name__ == '__main__':
    main()
