#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 12:29 PM
#  License: See LICENSE.txt
#


import logging
from beets import config as beets_global_config


MUST_HAVE_TRAINING_KEYS = ['song_bpm', 'song_len', 'duration', 'target']


def get_beets_logger():
    return logging.getLogger('beets.goingrunning')


def get_beets_global_config():
    return beets_global_config


def get_human_readable_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)

