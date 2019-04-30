# -*- coding: utf-8 -*-
"""
hierarchical prompt usage example
"""
from __future__ import print_function, unicode_literals

from PyInquirer import style_from_dict, prompt, Separator

from examples import custom_style_2

from math import floor

import pprint

input_landmarks = [
    "lndmark 1",
    "lndmark 2",
    "lndmark 3",
]

input_rois = [
    "roi 1",
    "roi 2",
    "roi 3",
]

TARGET_STR_LEN = 30

def pad_str_sep(input_str, target_len, pad_char):

    diff_len = target_len - len(input_str)

    pre_padding = pad_char * int(diff_len/2)
    post_padding = pad_char * int(diff_len/2 + diff_len % 1)

    rtn_str = pre_padding + " " + input_str + " "+ post_padding

    return Separator(rtn_str)

def make_main_menu_prompt(landmark_lst, roi_lst, curr_selection = None, roi_rep = 4):
    # make message
    message = "Main Menu: Select an option below."


    # construct landmark lst
    landmark_lst = [pad_str_sep("Landmarks:", TARGET_STR_LEN, "*")] + landmark_lst

    # make headers for roi seperators
    roi_sep = [pad_str_sep(x, TARGET_STR_LEN, "-") for x in roi_lst]

    # construct roi choices
    enum_rois = [["{} - {}".format(y, x) for x in range(1, roi_rep + 1)] for y in roi_lst]
    enum_rois = [[y] + x for x, y in zip(enum_rois, roi_sep)]
    enum_rois = [x for y in enum_rois for x in y]

    enum_rois = [pad_str_sep("ROIs:", TARGET_STR_LEN, "*")] + enum_rois

    # make choice list
    choice_lst = landmark_lst + enum_rois

    # construct prompt
    main_menu_prompt = {
        'type': 'list',
        'name': 'main_menu',
        'message': message,
        'choices': choice_lst,
    }

    return main_menu_prompt

def main():
    # get main menu prompt
    main_prompt = make_main_menu_prompt(input_landmarks, input_rois)

    answer = prompt(main_prompt)
    print(answer['main_menu'])

if __name__ == '__main__':
    main()
