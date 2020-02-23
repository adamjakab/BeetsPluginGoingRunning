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
from beets.random import random_objs

MUST_HAVE_TRAINING_KEYS = ['song_bpm', 'song_len', 'duration', 'target']


def get_beets_logger():
    return logging.getLogger('beets.goingrunning')


def get_beets_global_config():
    return beets_global_config


def get_human_readable_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


def get_config_value_bubble_up(cfg_view: Subview, attrib: str):
    """
    Method that will ''bubble up'' in the configuration hierarchy to find the value of the requested attribute
    """
    value = None

    if cfg_view[attrib].exists():
        value = cfg_view[attrib].get()
    else:
        view_name = cfg_view.name
        if view_name != "root":
            value = get_config_value_bubble_up(cfg_view.parent, attrib)

    return value


def get_duration_of_items(items):
    """
    Calculate the total duration of the media items using the "length" attribute
    :param items: list
    :return: int
    """
    total_time = 0

    if isinstance(items, list):
        for item in items:
            try:
                total_time += int(item.get("length"))
            except TypeError:
                pass
            except ValueError:
                pass

    return total_time


def get_randomized_items(items, duration_min):
    """ This randomization and limiting to duration_min is very basic
    @todo: after randomization select songs to be as close as possible to the duration_min (+-5seconds)
    """
    r_limit = 1
    r_time_minutes = duration_min
    r_equal_chance = True
    rnd_items = random_objs(list(items), False, r_limit, r_time_minutes, r_equal_chance)

    return rnd_items

