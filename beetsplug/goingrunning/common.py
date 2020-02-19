#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 12:29 PM
#  License: See LICENSE.txt
#


import logging
from beets import config as beets_global_config
from beets.util.confit import Subview
from collections import OrderedDict

MUST_HAVE_TRAINING_KEYS = ['song_bpm', 'song_len', 'duration', 'target']


def get_beets_logger():
    return logging.getLogger('beets.goingrunning')


def get_beets_global_config():
    return beets_global_config


def get_human_readable_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


def get_config_value_bubble_up(target: Subview, attrib: str):
    """
    Method that will ''bubble up'' in the configuration hierarchy to find the value of the requested attribute
    """
    value = None
    done = False

    while not done:
        tree: OrderedDict = target.flatten()
        if attrib in tree:
            value = tree.get(attrib)
            done = True
        else:
            if target.root() != target.parent:
                target: Subview = target.parent
            else:
                done = True

    return value

