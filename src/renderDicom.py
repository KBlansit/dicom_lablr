#!/usr/bin/env python

# import libraries
import sys
import math
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

initial_usr_msg = ", ".join([str(x) + " []" for x in valid_location_types]) + "\r"

class RenderDicomSeries:
    def __init__(self, ax, dicom_lst):
        # store imputs
        self.ax = ax
        self.dicom_lst = dicom_lst

        # set all circle_data and slice as None
        self.circle_data = {x: None for x in valid_location_types}
        self.circle_location = {x: None for x in valid_location_types}
        self.slice_location = {x: None for x in valid_location_types}

        # initialize current selections
        self.curr_selection = None
        self.curr_idx = 0
        self.scrolling = False

        # render to image
        self.im = self.ax.imshow(self.dicom_lst[self.curr_idx].pixel_array, cmap='gray')

        # finish initialiazation
        self._update_image(self.curr_idx)

        # determine
        sys.stdout.write("Slide 0; " + initial_usr_msg)
        sys.stdout.flush()

    def connect(self):
        """
        connection hooks
        """
        # keyboard press
        self.cid_keyboard_press = self.ax.figure.canvas.mpl_connect(
            'key_press_event', self._on_key_press)
        # click
        self.cid_click = self.ax.figure.canvas.mpl_connect(
            'button_press_event', self._on_click)
        # movement
        self.cid_movement = self.ax.figure.canvas.mpl_connect(
            'motion_notify_event', self._on_movement)
        # release
        self.cid_release = self.ax.figure.canvas.mpl_connect(
            'button_release_event', self._on_release)

    def disconnect(self):
        """
        disconnect
        """
        self.ax.figure.canvas.mpl_disconnect('key_press_event')
        self.ax.figure.canvas.mpl_disconnect('button_press_event')
        self.ax.figure.canvas.mpl_disconnect('button_release_event')

    def _update_image(self, new_idx):
        """
        INPUTS:
            new_idx:
                the index of self.dicom_lst to render
        EFFECT:
            updates
        """

        # set curr inde and image
        self.curr_idx = new_idx

        # render dicom image
        self.im.set_data(self.dicom_lst[self.curr_idx].pixel_array)

        # get x and y limits
        self.x_max = self.ax.get_xlim()[1]
        self.y_max = self.ax.get_ylim()[0]

        # determine if need to remove or re-draw circles
        for x in valid_location_types:
            if self.slice_location[x] == new_idx:
                self.circle_data[x].set_visible(True)
            elif self.slice_location[x] == None:
                pass
            elif self.circle_data[x] is not None:
                self.circle_data[x].set_visible(False)

        # update view
        self.ax.figure.canvas.draw()

    def _on_click(self, event):
        """
        """
        if event.button == 3:
            # update scrolling
            self.scrolling = True

            # determine necessary delta for movement
            # update vertical limit
            vert_lim = (self.im.figure.get_size_inches()*self.im.figure.dpi)[1]
            self.delta = math.floor(vert_lim/len(self.dicom_lst))

            # initialize curr x and y locations
            self.last_x, self.last_y = event.x, event.y

        else:
            # return if nothing is selected
            if self.curr_selection is None:
                return

            # test if already populated data to reset
            if self.circle_data[self.curr_selection] is not None:
                # remove old circle
                self.circle_data[self.curr_selection].remove()

            # create circle object
            circ = Circle((event.xdata, event.ydata), 1, edgecolor='red', fill=True)
            self.circle_data[self.curr_selection] = circ
            self.circle_data[self.curr_selection].PLOTTED = True
            self.ax.add_patch(circ)

            # add slice_location and circle location information
            self.slice_location[self.curr_selection] = self.curr_idx
            self.circle_location[self.curr_selection] = circ.center

            # draw image
            self.ax.figure.canvas.draw()

    def _on_movement(self, event):
        """
        """
        # determine if scrolling
        if self.scrolling:
            # determine current x and y events
            curr_x, curr_y = event.x, event.y

            # determine if moving up or down
            if (curr_y - self.last_y) >= self.delta:
                self.last_x, self.last_y = event.x, event.y
                self._next_image()
            elif -(curr_y - self.last_y) > self.delta:
                self.last_x, self.last_y = event.x, event.y
                self._prev_image()
            else:
                return
        else:
            return

    def _on_release(self, event):
        """
        """
        self.scrolling = False
        self._prev_x = None
        self._prev_y = None

        # return if nothing is selected
        if self.curr_selection is None:
            return

    def _on_key_press(self, event):
        """
        INPUTS:
            event:
                event object from matplotlib
        EFFECT:
            selects markers, moves slides, and prints informaiton
        """
        # return if not in list of c
        if event.key in str(locations_markers.keys()):
            # set to selection
            self.curr_selection = locations_markers[int(event.key)]
        elif event.key == "escape":
            self.curr_selection = None
        elif event.key == "up":
            self._prev_image()
        elif event.key == "down":
            self._next_image()
        else:
            return

        # print info to console
        curr_status = [""] * len(valid_location_types)

        # determine the elements that are already chosen
        for ind, x in enumerate(valid_location_types):
            if hasattr(self, "curr_selection"):
                if x == self.curr_selection:
                    curr_status[ind] = "X"
                elif self.slice_location[x] is not None:
                    curr_status[ind] = "slice: " + str(self.slice_location[x])

        # concatenate message
        if hasattr(self, "curr_selection"):
            usr_msg = ", ".join([x+" ["+y+"]" for x,y in zip(valid_location_types, curr_status)]) + "\r"
        else:
            usr_msg = initial_usr_msg

        usr_msg = "Slide: %d; " %  self.curr_idx + usr_msg

        # write message
        sys.stdout.write(usr_msg)
        sys.stdout.flush()

    def _add_circle_location(self, location_type):
        """
        """
        # return if not a valid selection
        if location_type not in valid_location_types:
            raise AssertionError("Location type not in predefined location types")


    def _next_image(self):
        if self.curr_idx == len(self.dicom_lst) - 1:
            return

        self._update_image(self.curr_idx + 1)

    def _prev_image(self):

        if self.curr_idx == 0:
            return

        self._update_image(self.curr_idx - 1)

def plotDicom(dicom_lst):
    """
    INPUTS:
        dicom:
            dicom object
    EFFECT:
        plots dicom object and acts as hook for GUI funcitons
    """

    # make fig object
    fig, (ax) = pyplot.subplots(1)

    # make figure
    ax.set_aspect('equal')
    cursor = Cursor(ax, useblit=True, color='red', linewidth=1)

    # connect to function
    dicomRenderer = RenderDicomSeries(ax, dicom_lst)
    dicomRenderer.connect()
    pyplot.show()

    # clean up
    dicomRenderer.disconnect()
