#!/usr/bin/env python

# import libraries
import re
import sys
import math
import dicom
import datetime

import numpy as np
import pandas as pd
import matplotlib as mpl

from matplotlib import pyplot, cm
from matplotlib.patches import Circle
from matplotlib.widgets import Cursor

# import user fefined libraries
from src.utility import import_anatomic_settings

# global messages
INITIAL_USR_MSG = "Please select a anatomic landmark"
CONTRAST_SCALE = 5

DEFAULT_Z_AROUND_CENTER = 2
DEFAULT_XY_RAD = 10

REGEX_PARSE = re.compile("([aA-zZ]+)")

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

# main class
class RenderDicomSeries:
    def __init__(self, ax, dicom_lst, settings_path, previous_path=None):

        # import settings
        settings = import_anatomic_settings(settings_path)

        if "anatomic_landmarks" in settings:
            self.locations_markers = settings["anatomic_landmarks"]
        else:
            raise IOError("settings file {} doesn't have anatomic_landmarks".format(settings_path))

        if "roi_landmarks" in settings:
            self.roi_landmarks = settings["roi_landmarks"]
        else:
            self.roi_landmarks = []

        self.valid_location_types = [v for k,v in self.locations_markers.items()]

        # store imputs
        self.ax = ax
        self.dicom_lst = dicom_lst

        # initialize current selections
        self.curr_selection = None
        self.curr_idx = 0
        self.scrolling = False

        # render to image
        self.im = self.ax.imshow(self.dicom_lst[self.curr_idx].pixel_array, cmap='gray')

        # remember default contrast
        self.default_contrast_window = self.im.get_clim()

        # load data if previous_path specified
        if previous_path is not None:
            # initialize circ data, bounds, and slice loc dicts
            self.circle_data = {}
            self.circle_bounds = {}
            self.slice_location = {}

            data_df = pd.read_csv(previous_path + "/data.csv", sep = ",")
            self.click_df = pd.read_csv(previous_path + "/timestamps.csv", sep = ",")

            # loop through rows
            for index, row in data_df.iterrows():
                # select curr markere
                curr_marker = row['location']

                # test if we actually have data
                if not row[["x", "y", "img_slice"]].isnull().sum():

                    # add circle data
                    curr_xy = row[["x", "y"]]
                    curr_radius = row["roi_xy_rad"] if not np.isnan(row["roi_xy_rad"]) else 1
                    curr_fill = np.isnan(row["roi_xy_rad"])
                    circ = Circle((curr_xy), curr_radius, edgecolor='red', fill=curr_fill)

                    self.circle_data[curr_marker] = circ
                    self.circle_data[curr_marker].PLOTTED = False
                    self.ax.add_patch(circ)

                    # add bounding data
                    self.circle_bounds[curr_marker] = row["roi_bounds"]

                    # add slice loc data
                    self.slice_location[curr_marker] = row['img_slice']

                # else set values to none
                else:
                    self.circle_data[curr_marker] = None
                    self.circle_bounds[curr_marker] = None
                    self.slice_location[curr_marker] = None

        # set all circle_data and slice as None
        else:
            self.circle_data = {x: None for x in self.valid_location_types}
            self.circle_bounds = {x: None for x in self.valid_location_types}
            self.slice_location = {x: None for x in self.valid_location_types}

            # initialize monitering dataframe
            self.click_df = pd.DataFrame(columns = ['timestamp', 'selection', 'type'])

        # finish initialiazation
        self._update_image(self.curr_idx)

        # determine
        sys.stdout.write("Slide 0; " + INITIAL_USR_MSG)
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

    def return_data(self):
        """
        OUTPUT:
            a pandas dataframe of the coordinates
        """
        # initialize df
        df = pd.DataFrame(columns = ["x", "y", "img_slice", "location", "rad", "z_len"])

        # iterate through anatomic types
        for location in self.valid_location_types:
            if self.circle_data[location] is None:
                x, y, img_slice, roi_xy_rad, roi_bounds = [[np.nan]] * 5
            else:
                x, y = self.circle_data[location].center
                img_slice = self.slice_location[location]
                x, y, img_slice = [x], [y], [img_slice]

                # for ROI markers
                if REGEX_PARSE.search(location).group() in self.roi_landmarks:
                    roi_xy_rad = self.circle_data[location].radius
                    roi_bounds = self.circle_bounds[location]
                else:
                    roi_xy_rad, roi_bounds = ([np.nan], [np.nan])

            tmp_df = pd.DataFrame({
                'x': x,
                'y': y,
                'img_slice': img_slice,
                'location': location,
                'roi_xy_rad': roi_xy_rad,
                'roi_bounds': roi_bounds,
            })
            df = df.append(tmp_df)

        return df, self.click_df

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
            if self.slice_location[x] == new_idx:
                self.circle_data[x].set_visible(True)
            elif self._eval_roi_bounds(x):
                self.circle_data[x].set_visible(True)
            elif self.slice_location[x] == None:
                pass
            elif self.circle_data[x] is not None:
                self.circle_data[x].set_visible(False)
            elif self._eval_roi_bounds(x):
                self.circle_data[x].set_visible(True)

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
            if self.circle_data[self.curr_selection] is not None:
                # get old circle radius data
                roi_xy_rad = self.circle_data[self.curr_selection].radius
                roi_bounds = self.circle_bounds[self.curr_selection]

                # remove old circle
                self.circle_data[self.curr_selection].remove()

            # create circle object
            if REGEX_PARSE.search(self.curr_selection).group() in self.roi_landmarks:
                # default settings if None
                roi_xy_rad = roi_xy_rad if roi_xy_rad != None else DEFAULT_XY_RAD
                roi_bounds = roi_bounds if roi_bounds != None else DEFAULT_Z_AROUND_CENTER

                # make new circle
                circ = Circle((event.xdata, event.ydata), roi_xy_rad, edgecolor='red', fill=False)

                # save bounds information to self
                self.circle_bounds[self.curr_selection] = roi_bounds
            else:
                circ = Circle((event.xdata, event.ydata), 1, edgecolor='red', fill=True)

            self.circle_data[self.curr_selection] = circ
            self.circle_data[self.curr_selection].PLOTTED = True
            self.ax.add_patch(circ)

            # add slice_location and circle location information
            self.slice_location[self.curr_selection] = self.curr_idx

            # add click information to dataframe
            self.click_df = self.click_df.append(pd.DataFrame({
                'timestamp':[datetime.datetime.now()],
                'selection':[self.curr_selection],
                'type': 'add'
            })).reindex()

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
            self._change_circle_size(1)
        elif event.key == "-":
            self._change_circle_size(-1)

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

    def _change_circle_size(self, direction):
        """
        INPUT:
            direction:
                the int direction of change for radius
        EFFECT:
            changes the size of the circle radius
        """
        # return if nothing is selected
        if self.curr_selection is None:
            return
        # return if slice location not valid
        elif self.slice_location[self.curr_selection] == None:
            return
        # anatomy is not a roi circle to change
        elif REGEX_PARSE.search(self.curr_selection).group() in self.roi_landmarks:
            # change size
            curr_rad = self.circle_data[self.curr_selection].radius
            self.circle_data[self.curr_selection].set_radius(curr_rad + (direction * 1))

            # rerender
            self.ax.figure.canvas.draw()
        else:
            return

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
        # don't change if we have less than zero slices
        elif self.circle_bounds[self.curr_selection] + direction < 0:
            return
        else:
            self.circle_bounds[self.curr_selection] =\
                self.circle_bounds[self.curr_selection] + direction
            self._update_image(self.curr_idx)

    def _eval_roi_bounds(self, location):
        """
        INPUTS:
            location:
                the current anatomic location
        RETURN:
            True if and only if:
                - if location is in roi_landmarks list
                - circle_bounds[location][1] is not none
                - slice is actuall within bounds
            False otherwise
        """
        curr_bounds = self.circle_bounds[location]
        curr_loc = self.slice_location[location]

        # test to see if location is wihtin roi_landmarks
        if not REGEX_PARSE.search(location).group() in self.roi_landmarks:
            return False
        elif curr_bounds == None:
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
            if self.slice_location[self.curr_selection] is not None:
                slice_loc = "slice " + str(self.slice_location[self.curr_selection])
            else:
                slice_loc = " - "

            usr_msg = "Current selection: " + self.curr_selection + "[" + slice_loc + "]"

        # concatenate messges
        usr_msg = "\r" + "Slide: %d; " %  self.curr_idx + usr_msg

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
        elif self.slice_location[self.curr_selection] == None:
            return

        # test if already populated data to reset
        if self.circle_data[self.curr_selection] is not None:
            # remove old circle
            self.circle_data[self.curr_selection].remove()

            # if it's dumb and it works, it ain't dumb...
            self.circle_data[self.curr_selection] = None

        # draw image
        self.ax.figure.canvas.draw()

        # remove slice location
        self.slice_location[self.curr_selection] =  None

        # add click information to dataframe
        self.click_df = self.click_df.append(pd.DataFrame({
            'timestamp':[datetime.datetime.now()],
            'selection':[self.curr_selection],
            'type': 'remove'
        })).reindex()

    def _next_image(self):
        """
        EFFECT:
            advance image
        """
        if self.curr_idx == len(self.dicom_lst) - 1:
            return

        self._update_image(self.curr_idx + 1)

    def _prev_image(self):
        """
        EFFECT:
            previous image
        """
        if self.curr_idx == 0:
            return

        self._update_image(self.curr_idx - 1)

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

def plotDicom(dicom_lst, cmd_args, previous_directory=None):
    """
    INPUTS:
        dicom:
            dicom object
    EFFECT:
        plots dicom object and acts as hook for GUI funcitons
    """
    # determine if loading previous data
    #if previous_directory is not None:


    # toggle off toolbar
    mpl.rcParams['toolbar'] = 'None'

    # make fig object
    fig, (ax) = pyplot.subplots(1)

    # make figure
    ax.set_aspect('equal')
    cursor = Cursor(ax, useblit=True, color='red', linewidth=1)

    # connect to function
    if previous_directory is None:
        dicomRenderer = RenderDicomSeries(ax, dicom_lst, cmd_args.settings)
    else:
        dicomRenderer = RenderDicomSeries(ax, dicom_lst, cmd_args.settings, previous_directory)

    dicomRenderer.connect()
    pyplot.show()

    # clean up
    dicomRenderer.disconnect()

    # save data
    out_data, click_df = dicomRenderer.return_data()
    out_data = out_data[['location', 'x', 'y', 'img_slice', 'roi_xy_rad', 'roi_bounds']]

    return out_data, click_df
