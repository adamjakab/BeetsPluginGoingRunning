#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 11:30 AM
#  License: See LICENSE.txt
#

# Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/15/20, 11:19 AM
#  License: See LICENSE.txt

import logging
from beets import config as beets_global_config
from beets.plugins import BeetsPlugin
from goingrunning.goingrunning_command import GoingRunningCommand


MUST_HAVE_TRAINING_KEYS = ['song_bpm', 'song_len', 'duration', 'target']


def get_beets_logger():
    return logging.getLogger('beets.goingrunning')


def get_beets_global_config():
    return beets_global_config


def get_human_readable_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


# Classes
class GoingRunningPlugin(BeetsPlugin):
    def __init__(self):
        super(GoingRunningPlugin, self).__init__()
        self.config.add({
            'targets': [],
            'target': False,
            'clean_target': False,
            'song_bpm': [90, 150],
            'song_len': [90, 240],
            'duration': 60
        })

    def commands(self):
        return [GoingRunningCommand(self.config)]
