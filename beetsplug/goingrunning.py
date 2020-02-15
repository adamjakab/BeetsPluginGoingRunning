# Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/15/20, 11:19 AM
#  License: See LICENSE.txt

import re
import os
import sys
import logging
from optparse import OptionParser

# import beets
from beets import importer, config
from beets.plugins import BeetsPlugin
from beets.ui import Subcommand, decargs, colorize, input_yn, UserError
from beets.library import ReadError
from beets.util import cpu_count, displayable_path, syspath

# Module methods
log = logging.getLogger('beets.check')


# Classes ###


class GoingRunningPlugin(BeetsPlugin):

    def __init__(self):
        super(GoingRunningPlugin, self).__init__()
        self.config.add({
            'dry-run': False,
            'trainings': {
                'slow': {
                    'bpm_min': 120,
                    'bpm_max': 145,
                },
                'medium': {
                    'bpm_min': 145,
                    'bpm_max': 165,
                },
                'fast': {
                    'bpm_min': 165,
                    'bpm_max': 220,
                },
            }
        })

    def commands(self):
        return [GoingRunningCommand(self.config)]


class GoingRunningCommand(Subcommand):
    quiet = False
    lib = None
    query = None
    parser = None

    def __init__(self, config):
        # self.threads = config['threads'].get(int)
        # self.check_integrity = config['integrity'].get(bool)

        self.parser = OptionParser(usage='%prog training_name [options] [ADDITIONAL_QUERY...]')

        self.parser.add_option(
            '-l', '--list',
            action='store_true', dest='list', default=False,
            help=u'list the preconfigured training you have'
        )

        self.parser.add_option(
            '-q', '--quiet',
            action='store_true', dest='quiet', default=False,
            help=u'keep quiet'
        )

        # Keep this at the end
        super(GoingRunningCommand, self).__init__(
            parser=self.parser,
            name='goingrunning',
            help=u'bring some music with you that matches your training'
        )

    def func(self, lib, options, arguments):
        self.quiet = options.quiet
        self.lib = lib
        arguments = decargs(arguments)
        self.query = arguments

        # You must either pass a training name or request listing
        if len(arguments) < 1 and not options.list:
            log.warning("You can either pass the name of a training or request a listing (--list)!")
            self.parser.print_help()
            return

        if options.list:
            self.list_trainings()
        else:
            self.handle_training()

    def list_trainings(self):
        log.debug("Listing trainings...")

    def handle_training(self):
        training = self.query[0]
        log.debug("Handling training: {}".format(training))


