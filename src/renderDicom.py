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
            "BLOOD_VESSEL_1",
            "BLOOD_VESSEL_2",
            "BLOOD_VESSEL_3",
            "BLOOD_VESSEL_4",
        ]

        # set all circle_data as (None, None)
        self.circle_data = {x: None for x in self.valid_location_types}

    def add_circle_location(self, location_type, circle, img):
        """
            location_type: the location that one wants to set
            circle: the circle object
        """
        if location_type not in self.valid_location_types:
            raise AssertionError("Location type not in predefined location types")

        # test if already populated data to reset
        if self.circle_data[location_type] is not None:
            # remove old circle
            self.circle_data[location_type].remove()

            # add new circle
            self.circle_data[location_type] = circle

        else:
            self.circle_data[location_type] = circle

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

        # the current blood vessle selected
        self.curr_selection = None

        self.locations_markers = {}

        self.locations_markers = {ind + 1: x for ind, x in enumerate(self.circ_collection.valid_location_types)}

    def connect(self):
        """
        connection hooks
        """
        # keyboard press
        self.cid_keyboard_press = self.img.figure.canvas.mpl_connect(
            'key_press_event', self._on_key_press)
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
        if event.key not in str(self.locations_markers.keys()):
            return

        # set to selection
        self.curr_selection = self.locations_markers[int(event.key)]

    def _on_click(self, event):
        """
        """
        # return if nothing is selected
        if self.curr_selection is None:
            return

        # select the

        # outer circle

        #self.outer_circ = Circle((event.xdata, event.ydata), 10, edgecolor='red', fill=False)
        #self.img.add_patch(self.outer_circ)

        # inner circle
        inner_circ = Circle((event.xdata, event.ydata), 1, edgecolor='red', fill=True)
        self.img.add_patch(inner_circ)

        print(self.curr_selection)
        self.circ_collection.add_circle_location(self.curr_selection, inner_circ, self.img)

        # draw image
        self.img.figure.canvas.draw()

    def _on_release(self, event):
        """
        """
        # return if nothing is selected
        if self.curr_selection is None:
            return

        # outer circle
        #self.outer_circ.remove()

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
