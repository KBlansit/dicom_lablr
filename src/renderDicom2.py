#!/usr/bin/env python

# import libraries
import sys
import dicom
import numpy as np

from matplotlib import pyplot, cm
from matplotlib.patches import Circle
from matplotlib.widgets import Cursor

# define valid location types and location markers
valid_location_types = [
    "BLOOD_VESSEL_1",
    "BLOOD_VESSEL_2",
    "BLOOD_VESSEL_3",
    "BLOOD_VESSEL_4",
]

locations_markers = {ind + 1: x for ind, x in enumerate(valid_location_types)}

class RenderDicomSeries:
    def __init__(self, dicom_lst):
        # store imputs
        self.dicom_list = dicom_lst

        # set all circle_data and location_data as None
        self.circle_data = {x: None for x in valid_location_types}
        self.location_data = {x: None for x in valid_location_types}

        # setup objects for rendering dicom
        fig, (self.img) = pyplot.subplots(1)
        self.img.set_aspect('equal')
        cursor = Cursor(self.img, useblit=True, color='red', linewidth=1)

        # initialize current selections
        self.curr_user_selection = None
        self.curr_img_idx = 0

        # initialize image rendering
        self._update_image(self.curr_img_idx)
        
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

    def _update_image(self, new_idx):
        """
        INPUTS:
            new_idx
        EFFECT:
        """

        # set curr inde and image
        self.curr_idx = new_idx
        self.curr_dicom = self.dicom_list[self.curr_idx]

        # render dicom image
        self.img.imshow(self.curr_dicom.pixel_array, cmap='gray')

        # get x and y limits
        self.x_max = self.img.get_xlim()[1]
        self.y_max = self.img.get_ylim()[0]

        # extend if index has not yet been reached
        if self.curr_idx <= len(self.circ_collection):
            self.circ_collection.append(CircleCollection())

        # set curr CircleCollection
        self.curr_collection = self.circ_collection[self.curr_idx]

        # iterate through circles to populate
        for location_type in valid_location_types:
            location = self.curr_collection.get_location(location_type)
            if location is not None:
                inner_circ = Circle(location, 1, edgecolor='red', fill=True)
                self.img.add_patch(inner_circ)

        # the current blood vessle selected
        self.curr_selection = None

        # update view
        self.img.figure.canvas.draw()

    def _on_key_press(self, event):
        """
        """
        # return if not in list of c
        if event.key in str(locations_markers.keys()):
            # set to selection
            self.curr_selection = locations_markers[int(event.key)]
        elif event.key == "7":
            self.curr_collection.remove_all_circles()
        elif event.key == "enter":
            self._next_image()
        elif event.key == "ctrl+enter":
            self._prev_image()
        else:
            return

    def _add_circle_location(self, location_type):
        """
        """
        # return if not a valid selection
        if location_type not in valid_location_types:
            raise AssertionError("Location type not in predefined location types")

        # test if already populated data to reset
        if self.circle_data[location_type] is not None:
            # remove old circle
            self.location_data[location_type].remove()

            # add new circle
            self.circle_data[location_type] = circle
        else:
            # add new circle
            self.circle_data[location_type] = circle
    def _next_image(self):
        if self.curr_idx == len(self.dicom_list) - 1:
            return

        self._update_image(self.curr_idx + 1)
        print "UPDATE"

    def _prev_image(self):
        if self.curr_idx == 0:
            return

        self._update_image(self.curr_idx - 1)
        print "BACK"
