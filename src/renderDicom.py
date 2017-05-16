#!/usr/bin/env python

# import libraries
import sys
import math
import dicom
import numpy as np
import pandas as pd
import matplotlib as mpl

from matplotlib import pyplot, cm
from matplotlib.patches import Circle
from matplotlib.widgets import Cursor

# import user fefined libraries
from utility import import_anatomic_settings

# global messages
marker_keys = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
    "q", "w", "e", "r", "t", "y", "u", "i", "o", "p",
 ]
initial_usr_msg = "Please select a anatomic landmark"

class RenderDicomSeries:
    def __init__(self, ax, dicom_lst, settings_path):
        # start
        # define valid location types and location markers
        self.valid_location_types = import_anatomic_settings(settings_path)
        self.locations_markers = dict(zip(marker_keys, self.valid_location_types))

        # store imputs
        self.ax = ax
        self.dicom_lst = dicom_lst

        # set all circle_data and slice as None
        self.circle_data = {x: None for x in self.valid_location_types}
        self.slice_location = {x: None for x in self.valid_location_types}

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

    def return_data(self):
        """
        OUTPUT:
        returns a pandas dataframe of the coordinates
        """
        # initialize df
        df = pd.DataFrame(columns = ["x", "y", "img_slice", "location"])

        # iterate through anatomic types
        for location in self.valid_location_types:
            if self.circle_data[location] is None:
                x, y, img_slice = [[np.nan]] * 3
            else:
                x, y = self.circle_data[location].center
                img_slice = self.slice_location[location]
                x, y, img_slice = [x], [y], [img_slice]
            tmp_df = pd.DataFrame({
                'x': x,
                'y': y,
                'img_slice': img_slice,
                'location': location,
            })
            df = df.append(tmp_df)

        return df

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
        for x in self.valid_location_types:
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
            INPUT:
                event:
                    the event object from matplotlib
            EFFECT:
                if right button is pressed, start scrolling
                if an anatomical landmark is selected, set location
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

        elif event.button == 1:
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

            # determine if moving up or down
            if (curr_y - self.last_y) >= self.delta:
                self.last_x, self.last_y = event.x, event.y
                self._prev_image()
            elif -(curr_y - self.last_y) > self.delta:
                self.last_x, self.last_y = event.x, event.y
                self._next_image()
            else:
                return

            # print console msg
            self._print_console_msg()
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
        if event.key in str(self.locations_markers.keys()):
            # set to selection
            self.curr_selection = self.locations_markers[event.key]

        # escape functions
        elif event.key == "escape":
            self.curr_selection = None
        elif event.key == "tab":
            # removes current selection
            self._reset_location()

        # scroll up and down
        elif event.key == "up":
            self._prev_image()
        elif event.key == "down":
            self._next_image()

        # return results
        elif event.key == "shift+enter":
            self._close()
        else:
            return

        # print console msg
        self._print_console_msg()

    def _print_console_msg(self):
        """
        EFFECT:
            prints current status to console
        """
        # determine if there's a slice chosen
        if self.curr_selection is None:
            usr_msg = initial_usr_msg
        else:
            # determine if slice has already been set
            if self.slice_location[self.curr_selection] is not None:
                slice_loc = "slice " + str(self.slice_location[self.curr_selection])
            else:
                slice_loc = " - "

            usr_msg = "Current selection: " + self.curr_selection + "[" + slice_loc + "]"
        usr_msg = "Slide: %d; " %  self.curr_idx + usr_msg
        usr_msg = "\r" + usr_msg

        ## determine if element is already chosen
        #for ind, x in enumerate(self.valid_location_types):
        #    if hasattr(self, "curr_selection"):
        #        if x == self.curr_selection:
        #            curr_status[ind] = "X"
        #        elif self.slice_location[x] is not None:
        #            curr_status[ind] = "slice: " + str(self.slice_location[x])
#
        ## concatenate message
        #if hasattr(self, "curr_selection"):
        #    usr_msg = ", ".join([x+" ["+y+"]" for x,y in zip(self.valid_location_types, curr_status)]) + "\r"
        #else:
        #    usr_msg = initial_usr_msg
#
        #usr_msg = "Slide: %d; " %  self.curr_idx + usr_msg

        # write message
        sys.stdout.write(usr_msg.ljust(80))
        sys.stdout.flush()

    def _reset_location(self):
        """
        EFFECT:
            resets the location
        """
        # safe way to remove circle
        if self.circle_data[self.curr_selection] is not None:
            # remove old circle
            self.circle_data[self.curr_selection].remove()

            # draw image
            self.ax.figure.canvas.draw()

        # add slice_location and circle location information
        self.slice_location[self.curr_selection] = None

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

    def _close(self):
        """
        EFFECT:
            closes instance
        """
        pyplot.close()

def plotDicom(dicom_lst, cmd_args):
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
    cursor = Cursor(ax, useblit=True, color='red', linewidth=1)

    # connect to function
    dicomRenderer = RenderDicomSeries(ax, dicom_lst, cmd_args.settings)
    dicomRenderer.connect()
    pyplot.show()

    # clean up
    dicomRenderer.disconnect()

    # save data
    out_data = dicomRenderer.return_data()
    out_data = out_data[['location', 'x', 'y', 'img_slice']]

    return out_data
