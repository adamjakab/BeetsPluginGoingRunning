#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 11:30 AM
#  License: See LICENSE.txt
#

from beets.plugins import BeetsPlugin
from beetsplug.goingrunning.command import GoingRunningCommand


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
