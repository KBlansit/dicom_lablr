#!/usr/bin/env python

# import libraries
import re
import sys
import math
import dicom
import datetime

import numpy as np
import pandas as pd
import deepdish as dd
import matplotlib as mpl

from math import floor
from matplotlib import pyplot, cm, path, patches
from matplotlib.patches import Circle
from matplotlib.widgets import Cursor, LassoSelector, RectangleSelector

# import user fefined libraries
from src.utility import import_anatomic_settings, REGEX_PARSE
from src.process_roi import get_roi_indicies

# global messages
INITIAL_USR_MSG = "Please select a anatomic landmark"
CONTRAST_SCALE = 5

DEFAULT_Z_AROUND_CENTER = 0

COLOR_MAP = [
    "blue",
    "green",
    "orange",
    "red",
    "yellow",
    "teal",
    "pink",
]

# disable key maps
mpl.rcParams['keymap.fullscreen'] = ''
mpl.rcParams['keymap.home'] = ''
mpl.rcParams['keymap.back'] = ''
mpl.rcParams['keymap.forward'] = ''
mpl.rcParams['keymap.pan'] = ''
mpl.rcParams['keymap.zoom'] = ''
mpl.rcParams['keymap.save'] = ''
mpl.rcParams['keymap.quit'] = ''
mpl.rcParams['keymap.grid'] = ''
mpl.rcParams['keymap.yscale'] = ''
mpl.rcParams['keymap.xscale'] = ''
mpl.rcParams['keymap.all_axes'] = ''

KEY_PARSE = re.compile("([A-Z]+)([0-9]+)")

# main class
class RenderDicomSeries:
    def __init__(self, ax, dicom_lst, settings_path, previous_path=None):
        # import settings
        settings = import_anatomic_settings(settings_path)

        if "anatomic_landmarks" in settings:
            self.locations_markers = settings["anatomic_landmarks"]
        else:
            raise IOError("settings file {} doesn't have anatomic_landmarks".format(settings_path))

        # set roi_landmarks
        if "roi_landmarks" in settings:
            # filter roi landmarks
            roi_lst = []
            point_lst = []
            for lndmrk in self.locations_markers.values():
                if REGEX_PARSE.search(lndmrk).group() in settings["roi_landmarks"]:
                    roi_lst.append(lndmrk)
                else:
                    point_lst.append(lndmrk)

            self.roi_colors = dict(zip(settings["roi_landmarks"], COLOR_MAP))

        # initialize valid location types list
        self.valid_location_types = [v for k,v in self.locations_markers.items()]

        # store imputs
        self.ax = ax
        self.dicom_lst = dicom_lst

        # initialize current selections
        self.curr_selection = None
        self.curr_idx = 0
        self.scrolling = False

        # determine if we are using a cine series
        self.cine_series = self.dicom_lst[0].CardiacNumberOfImages

        # render to image
        self.im = self.ax.imshow(self.dicom_lst[self.curr_idx].pixel_array, cmap='gray')

        # remember default contrast
        self.default_contrast_window = self.im.get_clim()

        # load data if previous_path specified
        if previous_path is not None:
            # load dictionaries
            self.data_dict = dd.io.load(previous_path)

            # initialize old circle data
            self.circle_data = {}
            self.roi_data = {}
            for lndmrk, loc in self.data_dict["point_locations"].items():
                if loc:
                    circ = Circle((loc), 1, edgecolor='red', fill=True)
                    self.circle_data[lndmrk] = circ
                    self.circle_data[lndmrk].PLOTTED = False
                    self.ax.add_patch(circ)
                else:
                    self.circle_data[lndmrk] = None

            for curr_roi, ver_path in self.data_dict["vert_data"].items():
                if ver_path:
                    curr_class = REGEX_PARSE.search(curr_roi).group()
                    curr_color = self.roi_colors[curr_class]
                    patch = patches.PathPatch(ver_path, facecolor=curr_color, alpha = 0.4)
                    self.roi_data[curr_roi] = patch
                    patch.set_visible(False)
                    self.ax.add_patch(patch)
                else:
                    self.roi_data[curr_roi] = None

        else:
            # initialize data dict
            self.data_dict = {
                # all
                "slice_location": dict(zip(point_lst+roi_lst, [None for x in point_lst+roi_lst])),
                # point
                "point_locations": dict(zip(point_lst, [None for x in point_lst])),
                # roi
                "vert_data": dict(zip(roi_lst, [None for x in roi_lst])),
                "roi_bounds": dict(zip(roi_lst, [None for x in roi_lst])),
            }

            # initialize old circle data
            self.circle_data = dict(zip(point_lst, [None for x in point_lst]))
            self.roi_data = dict(zip(roi_lst, [None for x in roi_lst]))

        # finish initialiazation
        self._update_image(self.curr_idx)

        # determine
        sys.stdout.write("Slide 0; " + INITIAL_USR_MSG)
        sys.stdout.flush()

        # initialize lasso selector
        self.curr_lasso = LassoSelector(self.ax, self._lasso, button=1)
        self.curr_lasso.active = False

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
        EFFECT:
            disconnect
        """
        self.ax.figure.canvas.mpl_disconnect('key_press_event')
        self.ax.figure.canvas.mpl_disconnect('button_press_event')
        self.ax.figure.canvas.mpl_disconnect('button_release_event')

    def return_data(self):
        """
        OUTPUT:
            returns data dict
        """
        # get dicom acc id
        self.data_dict["acc_num"] = self.dicom_lst[0].AccessionNumber

        # return
        return self.data_dict

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

        # iterate through anatomies to determine if we redraw
        for x in self.valid_location_types:
            if self.data_dict["slice_location"][x] == new_idx:
                if x in self.roi_data.keys():
                    if self.roi_data[x] is not None:
                        self.roi_data[x].set_visible(True)
                else:
                    if self.circle_data[x] is not None:
                        self.circle_data[x].set_visible(True)
            elif self._eval_roi_bounds(x) and self.roi_data[x] is not None:
                self.roi_data[x].set_visible(True)
            elif self.data_dict["slice_location"][x] == None:
                pass
            elif x in self.roi_data.keys():
                if self.roi_data[x] is not None:
                    self.roi_data[x].set_visible(False)
            else:
                if self.circle_data[x] is not None:
                    self.circle_data[x].set_visible(False)

        # update view
        self.ax.figure.canvas.draw()

    def _on_click(self, event):
        """
        INPUT:
            event:
                the event object from matplotlib
        EFFECT:
            if correct button is pressed, start scrolling
            if an anatomical landmark is selected, set location
        """
        if event.button == 3:
            # update scrolling
            self.scrolling = True

            # initialize curr x and y locations
            self.last_x, self.last_y = event.x, event.y

            # draw image
            self.ax.figure.canvas.draw()

        elif event.button == 1:
            # return if nothing is selected
            if self.curr_selection is None:
                return

            # set default xy_circle_rad
            roi_xy_rad = None
            roi_bounds = None

            # test if already populated data to reset
            if self.curr_selection in self.circle_data:
                if self.circle_data[self.curr_selection] is not None:

                    # remove old circle
                    self.circle_data[self.curr_selection].remove()

            # create circle object
            if not self.curr_selection in self.roi_data.keys():
                circ = Circle((event.xdata, event.ydata), 1, edgecolor='red', fill=True)

                self.circle_data[self.curr_selection] = circ
                self.circle_data[self.curr_selection].PLOTTED = True
                self.ax.add_patch(circ)

                # add slice_location and circle location information
                self.data_dict["slice_location"][self.curr_selection] = self.curr_idx
                self.data_dict["point_locations"][self.curr_selection] = (event.xdata, event.ydata)

            # draw image
            self.ax.figure.canvas.draw()

    def _on_movement(self, event):
        """
            INPUT:
                event:
                    the event object from matplotlib
            EFFECT:
                scroll up/down slides
        """
        # determine if scrolling
        if self.scrolling:
            # determine current x and y events
            curr_x, curr_y = event.x, event.y

            # vertical movement
            delta_y = curr_y - self.last_y
            self._shift_contrast_window(delta_y * CONTRAST_SCALE)

            # horizontal movement
            delta_x = curr_x - self.last_x
            self._increase_contrast_window(delta_x * CONTRAST_SCALE)

            # update movement data
            self.last_x, self.last_y = event.x, event.y

        else:
            return

    def _on_release(self, event):
        """
        INPUT:
            event:
                the event object from matplotlib
        EFFECT:
            reset scrolling
        """
        # reset values
        self.scrolling = False
        self._prev_x = None
        self._prev_y = None

        # print
        self._print_console_msg()

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
        if event.key in self.locations_markers.keys():
            # set to selection
            self.curr_selection = self.locations_markers[event.key]

            # change lasso slector policy
            if self.curr_selection in self.roi_data.keys():
                self.curr_lasso.active = True
            else:
                self.curr_lasso.active = False

        # escape functions
        elif event.key == "escape":
            self.curr_selection = None

        # removes current selection
        elif event.key == "delete":
            self._reset_location()
        elif event.key == "backspace":
            self._reset_location()

        # scroll up and down
        elif event.key == "up":
            self._prev_image()
        elif event.key == "down":
            self._next_image()

        # advance cine
        elif event.key == "right":
            self._advance_cine_forward()
        elif event.key == "left":
            self._advance_cine_backward()

        # page up and down
        elif event.key == "pageup":
            for _ in range(10):
                self._prev_image()
        elif event.key == "pagedown":
            for _ in range(10):
                self._next_image()

        # resets contrast window
        elif event.key == "v":
            self.im.set_clim(self.default_contrast_window)
            self.ax.figure.canvas.draw()

        # return results
        elif event.key == "return":
            self._close()
        elif event.key == "enter":
            self._close()

        # change radius of current circle if a ROI landmark
        elif event.key == "+":
            self._change_z_bounds(1)
        elif event.key == "-":
            self._change_z_bounds(-1)

        # change z bounds around true slice
        elif event.key == "}":
            self._change_z_bounds(1)
        elif event.key == "{":
            self._change_z_bounds(-1)

        elif event.key == "]":
            self._change_z_bounds(1)
        elif event.key == "[":
            self._change_z_bounds(-1)

        # else quit
        else:
            return

        # print console msg
        self._print_console_msg()

    def _lasso(self, verts):
        """
        updates roi
        """
        # test if current key is a roi key
        if self.curr_selection in self.roi_data.keys():

            # remove old
            self._reset_location()

            # save verts indicies
            ver_path = path.Path(verts)
            self.data_dict["vert_data"][self.curr_selection] = ver_path

            # save patch
            curr_class = REGEX_PARSE.search(self.curr_selection).group()
            curr_color = self.roi_colors[curr_class]
            patch = patches.PathPatch(ver_path, facecolor=curr_color, alpha = 0.4)
            self.roi_data[self.curr_selection] = patch
            self.ax.add_patch(patch)

            # add slice_location and circle location information
            self.data_dict["slice_location"][self.curr_selection] = self.curr_idx
            self.data_dict["roi_bounds"][self.curr_selection] = DEFAULT_Z_AROUND_CENTER

            # update image
            self._update_image(self.curr_idx)

    def _change_z_bounds(self, direction):
        """
        INPUT:
            direction:
                the int direction of change for z bounds
        EFFECT:
            changes the size of the circle radius
        """
        # return if nothing is selected
        if self.curr_selection is None:
            return
        # return if we aren't in a valid roi type
        elif self.curr_selection not in self.roi_data.keys():
            return
        # don't change if we have less than zero slices
        elif self.data_dict["roi_bounds"][self.curr_selection] + direction < 0:
            return
        else:
            self.data_dict["roi_bounds"][self.curr_selection] =\
                self.data_dict["roi_bounds"][self.curr_selection] + direction

            # update image
            self._update_image(self.curr_idx)

            # update measurements
            self._update_attenuation()

    def _eval_roi_bounds(self, location):
        """
        INPUTS:
            location:
                the current anatomic location
        RETURN:
            True if and only if:
                - if location is in roi_data list
                - roi_bounds[location][1] is not none
                - slice is actuall within bounds
            False otherwise
        """
        if location in self.roi_data:
            curr_bounds = self.data_dict["roi_bounds"][location]
            curr_loc = self.data_dict["slice_location"][location]
        else:
            return False

        # test to see if location is wihtin roi_landmarks
        if curr_bounds == None or curr_loc == None:
            return False
        elif curr_loc - curr_bounds <= self.curr_idx <= curr_loc + curr_bounds:
            return True
        else:
            return False

    def _print_console_msg(self):
        """
        EFFECT:
            prints current status to console
        """
        # determine if there's a slice chosen
        if self.curr_selection is None:
            usr_msg = INITIAL_USR_MSG
        else:
            # determine if slice has already been set
            if self.curr_selection in self.roi_data:
                if self.roi_data[self.curr_selection] is not None:
                    # get vars
                    curr_loc = self.data_dict["slice_location"][self.curr_selection]
                    curr_bounds = self.data_dict["roi_bounds"][self.curr_selection]

                    # get max and min slice
                    min_slice = max(0, curr_loc - curr_bounds)
                    max_slice = min(len(self.dicom_lst), curr_loc + curr_bounds)

                    # construct string
                    slice_loc_str = " [slice - ({} - {} - {})]".format(*(str(x) for x in (min_slice, curr_loc, max_slice)))

                else:
                    slice_loc_str = ""

                # get curr roi type
                curr_roi = REGEX_PARSE.search(self.curr_selection).group()

            elif self.curr_selection in self.circle_data:
                if self.circle_data[self.curr_selection] is not None:
                    slice_loc_str = " [slice - {}]".format(str(self.data_dict["slice_location"][self.curr_selection]))
                else:
                    slice_loc_str = ""

            usr_msg = "Current selection: {}{}".format(self.curr_selection, slice_loc_str)

        # concatenate messges
        usr_msg = "\rSlide {}; {}".format(str(self.curr_idx), usr_msg)

        # write message
        sys.stdout.write(usr_msg.ljust(80))
        sys.stdout.flush()

    def _reset_location(self):
        """
        EFFECT:
            resets the location
        """
        # return if nothing is selected
        if self.curr_selection is None:
            return
        # return if slice location not valid
        elif self.data_dict["slice_location"][self.curr_selection] == None:
            return

        # test if it's an roi
        if self.curr_selection in self.roi_data.keys():
            # test if already populated data to reset
            if self.roi_data[self.curr_selection] is not None:
                self.roi_data[self.curr_selection].remove()
                self.roi_data[self.curr_selection] = None
                self.data_dict["vert_data"][self.curr_selection] = None
            else:
                return

        # remove for point location anatomy data
        else:
            # test if already populated data to reset
            if self.circle_data[self.curr_selection] is not None:
                # remove old circle
                self.circle_data[self.curr_selection].remove()
                self.circle_data[self.curr_selection] = None

                # remove slice location
                self.data_dict["slice_location"][self.curr_selection] =  None
            else:
                return

        # update measurements
        self._update_attenuation()

        # draw image
        self.ax.figure.canvas.draw()

    def _next_image(self):
        """
        EFFECT:
            advance image
        """
        if self.cine_series:
            indx_advance = self.curr_idx + self.cine_series
        else:
            indx_advance = self.curr_idx + 1

        if indx_advance >= len(self.dicom_lst) - 1:
            return

        self._update_image(indx_advance)

    def _prev_image(self):
        """
        EFFECT:
            previous image
        """
        if self.cine_series:
            indx_advance = self.curr_idx - self.cine_series
        else:
            indx_advance = self.curr_idx - 1

        if indx_advance < 0:
            return

        self._update_image(indx_advance)

    def _advance_cine_forward(self):
        """
        effect:
            for dicom series that have cine frames, advances forward a cine frame
        """

        if not self.cine_series:
            return
        else:
            curr_slice = floor(self.curr_idx/self.cine_series)
            indx_advance = (curr_slice * self.cine_series) + ((self.curr_idx + 1)% self.cine_series)

        if indx_advance >= len(self.dicom_lst) - 1:
            return

        self._update_image(indx_advance)

    def _advance_cine_backward(self):
        """
        effect:
            for dicom series that have cine frames, advances backward a cine frame
        """
        if not self.cine_series:
            return
        else:
            curr_slice = floor(self.curr_idx/self.cine_series)
            indx_advance = (curr_slice * self.cine_series) + ((self.curr_idx - 1)% self.cine_series)

        if indx_advance < 0:
            return

        self._update_image(indx_advance)

    def _increase_contrast_window(self, delta):
        """
        EFFECT:
            increases contrast window
        """
        # limits on delta
        if abs(delta) > 500:
            if delta > 0:
                delta = 500
            else:
                delta = -500

        # get current contrast
        curr_clim = self.im.get_clim()

        half_delta = delta/2.

        self.im.set_clim(curr_clim[0] - half_delta, curr_clim[1] + half_delta)

        # draw image
        self.ax.figure.canvas.draw()

    def _shift_contrast_window(self, delta):
        """
        EFFECT:
            shifts contrast window
        """
        # limits on delta
        if abs(delta) > 500:
            if delta > 0:
                delta = 500
            else:
                delta = -500

        # get current contrast
        curr_clim = self.im.get_clim()

        half_delta = delta/2

        self.im.set_clim(curr_clim[0] + half_delta, curr_clim[1] + half_delta)

        # draw image
        self.ax.figure.canvas.draw()

    def _close(self):
        """
        EFFECT:
            closes instance
        """
        pyplot.close()

def plotDicom(dicom_lst, settings_path, previous_directory=None):
    """
    INPUTS:
        dicom:
            dicom object
    EFFECT:
        plots dicom object and acts as hook for GUI funcitons
    """
    # toggle off toolbar
    mpl.rcParams['toolbar'] = 'None'

    # make fig object
    fig, (ax) = pyplot.subplots(1)

    # make figure
    ax.set_aspect('equal')
    ax.axis('off')
    cursor = Cursor(ax, useblit=True, color='red', linewidth=1)

    # connect to function
    if previous_directory is None:
        dicomRenderer = RenderDicomSeries(ax, dicom_lst, settings_path)
    else:
        dicomRenderer = RenderDicomSeries(ax, dicom_lst, settings_path, previous_directory)

    dicomRenderer.connect()
    pyplot.show()

    # clean up
    dicomRenderer.disconnect()

    # save data
    return dicomRenderer.return_data()
