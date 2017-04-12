#!/usr/bin/env python

# import libraries
import sys
import dicom
import numpy as np

from matplotlib import pyplot, cm
from matplotlib.patches import Circle
from matplotlib.widgets import Cursor

class MarkerBuilder:
    def __init__(self, img):
        # set self object
        self.img = img

        # get x and y limits
        self.x_max = img.get_xlim()[1]
        self.y_max = img.get_ylim()[0]
        print("x max: " + str(self.x_max) + " y max: " + str(self.y_max))

        self.click = None
    def connect(self):
        """
        connection hooks
        """
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
        self.img.figure.canvas.mpl_disconnect('button_press_event')
        self.img.figure.canvas.mpl_disconnect('button_release_event')



    def _on_click(self, event):
        """
        """
        sys.stdout.write("x: %d, y: %d\r" % (event.x, event.y))
        sys.stdout.flush()


    def _on_release(self, event):
        """
        """
        # outer circle
        self.outer_circ = Circle((event.xdata, event.ydata), 10, edgecolor='red', fill=False)
        self.img.add_patch(self.outer_circ)

        # inner circle
        self.inner_circ = Circle((event.xdata, event.ydata), 1, edgecolor='red', fill=True)
        self.img.add_patch(self.inner_circ)

        self.img.figure.canvas.draw()


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
    cursor = Cursor(ax, useblit=True, color='red', linewidth=1)

    # connect to function
    mb = MarkerBuilder(ax)
    mb.connect()

    #pyplot.connect('motion_notify_event', fun1)

    # render
    pyplot.show()

    # clean up
    mb.disconnect()
