#!/usr/bin/env python

# import libraries
import sys
import dicom
import numpy as np

from matplotlib import pyplot, cm
from matplotlib.patches import Circle
from matplotlib.widgets import Cursor

class CircleCollection:
    def __init__(self):
        # initialize valid circle locations
        self.valid_location_types = [
            "BLOOD_VESSLE_1",
            "BLOOD_VESSLE_2",
            "BLOOD_VESSLE_3",
            "BLOOD_VESSLE_4",
        ]

        # set all circle_locations as (None, None)
        {x: (None, None) for x in self.valid_location_types}

    def add_circle_location(self, location_type):
        """
        """
        if location_type not in self.valid_location_types:
            raise AssertionError("Location type not in predefined location types")

    def retrieve_all_locations(self):
        """
        """

class MarkerBuilder:
    def __init__(self, img):
        # set self object
        self.img = img

        # get x and y limits
        self.x_max = img.get_xlim()[1]
        self.y_max = img.get_ylim()[0]

        # collection of circles
        self.circ_collection = CircleCollection()
        self.circ_collection.valid_location_types

        # the current blood vessle selected
        self.curr_selection = None

        # TODO: refactor
        self.locations_markers = {
            1: "BLOOD_VESSLE_1",
            2: "BLOOD_VESSLE_2",
            3: "BLOOD_VESSLE_3",
            4: "BLOOD_VESSLE_4",
        }

    def connect(self):
        """
        connection hooks
        """
        # keyboard press
        self.cid_keyboard_press = self.img.figure.canvas.mpl_connect(
        'key_press_event', self._on_release)
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
        self.img.figure.canvas.mpl_disconnect('key_press_event')
        self.img.figure.canvas.mpl_disconnect('button_press_event')
        self.img.figure.canvas.mpl_disconnect('button_release_event')

    def _on_key_press(self, event):
        """
        """
        # return if not in list of c
        if event.key not in self.locations_markers.keys():
            return


    def _on_click(self, event):
        """
        """
        # outer circle
        self.outer_circ = Circle((event.xdata, event.ydata), 10, edgecolor='red', fill=False)
        self.img.add_patch(self.outer_circ)

        # inner circle
        self.inner_circ = Circle((event.xdata, event.ydata), 1, edgecolor='red', fill=True)
        self.img.add_patch(self.inner_circ)

        self.img.figure.canvas.draw()

        # skip if there is no selection
        if self.curr_selection is None:
            return

    def _on_release(self, event):
        """
        """
        # outer circle
        self.outer_circ.remove()

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
