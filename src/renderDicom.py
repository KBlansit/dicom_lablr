#!/usr/bin/env python

# import libraries
import sys
import dicom
import numpy as np

from matplotlib import pyplot, cm
from matplotlib.patches import Circle

class MarkerBuilder:
    def __init__(self, img):
        # set self object
        self.img = img

        # get x and y limits
        self.xs = img.get_xlim()[0]
        self.ys = img.get_ylim()[0]

    def connect(self):
        """
        connection hooks
        """
        # motion
        self.cid_motion = self.img.figure.canvas.mpl_connect(
            'motion_notify_event', self._on_motion)
        # click
        self.cid_click = self.img.figure.canvas.mpl_connect(
            'button_press_event', self._on_click)
        # release
        self.cid_release = self.img.figure.canvas.mpl_connect(
            'button_release_event', self._on_release)

    def disconnect(self):
        """
        disconnect
        """
        self.img.figure.canvas.mpl_disconnect('motion_notify_event')
        self.img.figure.canvas.mpl_disconnect('motion_notify_event')
        self.img.figure.canvas.mpl_disconnect('motion_notify_event')

    def _on_motion(self, event):
        """
        move the circle
        """
        sys.stdout.write("x: %d, y: %d\r" % (event.x, event.y))
        sys.stdout.flush()

    def _on_click(self, event):
        """
        """
        print("click on")
        sys.stdout.flush()

    def _on_release(self, event):
        """
        """
        print("click off")
        sys.stdout.flush()


# functions to contorl
def fun1(event):
    sys.stdout.write("x: %d, y: %d\r" % (event.x, event.y))
    sys.stdout.flush()

# primary dicom hook
def plotDicom(dicom):
    """
    inputs:
        dicom:
            dicom object
    effect:
        plots dicom object and acts as hook for GUI funcitons
    """

    # make fig object
    fig, (ax) = pyplot.subplots(1)

    # make figure
    ax.set_aspect('equal')
    ax.imshow(dicom.pixel_array, cmap='gray')

    ax.add_patch(Circle((250, 250), 10, edgecolor='red', fill=False))

    # connect to function
    mb = MarkerBuilder(ax)
    mb.connect()

    #pyplot.connect('motion_notify_event', fun1)

    # render
    pyplot.show()

    # clean up
    mb.disconnect()
