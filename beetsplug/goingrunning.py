# Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/15/20, 11:19 AM
#  License: See LICENSE.txt

from beets.plugins import BeetsPlugin
from beets.ui import Subcommand


def command_body(lib, opts, args):
    print("Are you going running?")


going_running_command = Subcommand('goingrunning', help='bring some music with you that matches your training')
going_running_command.func = command_body


class GoingRunningPlugin(BeetsPlugin):
    def commands(self):
        return [going_running_command]

