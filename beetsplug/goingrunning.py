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
from beets import config as beets_global_config
from beets.library import Library as BeatsLibrary
from beets.plugins import BeetsPlugin
from beets.ui import Subcommand, decargs, colorize, input_yn, UserError
from beets.library import ReadError
from beets.util import cpu_count, displayable_path, syspath

# Module methods
log = logging.getLogger('beets.check')


def get_beets_global_config():
    return beets_global_config.flatten()


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
    config = None
    quiet = False
    lib = None
    query = None
    parser = None

    def __init__(self, cfg):
        self.config = cfg.flatten()
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

    def func(self, lib: BeatsLibrary, options, arguments):
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

    # @todo: explain keys
    # @todo: order keys
    def list_trainings(self):
        self._say("List trainings:")
        training_names = list(self.config["trainings"].keys())
        for training_name in training_names:
            self.list_training_attributes(training_name)

    def list_training_attributes(self, training_name):
        self._say("{0} ::: {1}".format("=" * 40, training_name))
        training = self.config["trainings"].get(training_name)
        tkeys = training.keys()
        for tkey in tkeys:
            tval = training.get(tkey)
            self._say("{0} : {1}".format(tkey, tval))

    def handle_training(self):
        training_name = self.query[0]
        training = self.config["trainings"].get(training_name)
        if not training:
            log.warning("There is no training registered with this name!")
            return

        self._say("Handling training: {}".format(training_name))
        self.list_training_attributes(training_name)

        i = self.lib.items()
        print(i)


    def _say(self, msg):
        if not self.quiet:
            log.info(msg)
        else:
            log.debug(msg)
