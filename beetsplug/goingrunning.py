# Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/15/20, 11:19 AM
#  License: See LICENSE.txt

import random
import os
import string
import logging
from collections import OrderedDict
from optparse import OptionParser
from pathlib import Path

from shutil import copyfile
from glob import glob
from beets import config as beets_global_config
from beets.dbcore.db import Results
from beets.library import Library as BeatsLibrary, Item
from beets.plugins import BeetsPlugin
from beets.random import random_objs
from beets.ui import Subcommand, decargs
from beets.library import ReadError
from beets.util import cpu_count, displayable_path, syspath

# Module methods
from beets.util.confit import ConfigView, Subview, ConfigTypeError


DEFAULT_TRAINING_KEYS = ['song_bpm', 'song_len', 'duration', 'target']


log = logging.getLogger('beets.goingrunning')


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
            'song_len': [90, 150],
            'duration': 60
        })

    def commands(self):
        return [GoingRunningCommand(self.config)]


class GoingRunningCommand(Subcommand):
    config: Subview = None
    lib = None
    query = None
    parser = None

    quiet = False
    count_only = False

    def __init__(self, cfg):
        self.config = cfg
        # self.threads = config['threads'].get(int)
        # self.check_integrity = config['integrity'].get(bool)

        self.parser = OptionParser(usage='%prog training_name [options] [ADDITIONAL_QUERY...]')

        self.parser.add_option(
            '-l', '--list',
            action='store_true', dest='list', default=False,
            help=u'list the preconfigured training you have'
        )

        self.parser.add_option(
            '-c', '--count',
            action='store_true', dest='count', default=False,
            help=u'count the number of songs available for a specific training'
        )

        # @todo: add dry-run option

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
        self.count_only = options.count

        self.lib = lib
        self.query = decargs(arguments)

        # You must either pass a training name or request listing
        if len(self.query) < 1 and not options.list:
            log.warning("You can either pass the name of a training or request a listing (--list)!")
            self.parser.print_help()
            return

        if options.list:
            self.list_trainings()
        else:
            self.handle_training()

    def handle_training(self):
        training_name = self.query.pop(0)

        training: Subview = self.config["trainings"][training_name]
        if not training:
            self._say("There is no training registered with this name!")
            return

        # Get the library items
        lib_items: Results = self._retrieve_library_items(training)

        # Show count only
        if self.count_only:
            self._say("Number of songs: {}".format(len(lib_items)))
            return

        # Verify target
        target_path = self._get_target_path(training)
        if not os.path.isdir(target_path):
            target_name = self._get_config_value_bubble_up(training, "target")
            self._say("The path for the target[{0}] does not exist! Path: {1}".format(target_name, target_path))
            return

        self._say("Handling training: {}".format(training_name))

        # Get randomized items
        duration = self._get_config_value_bubble_up(training, "duration")
        rnd_items = self._get_randomized_items(lib_items, duration)

        # Show some info
        total_time = self._get_duration_of_items(rnd_items)
        self._say("Total song time: {}".format(get_human_readable_time(total_time)))
        self._say("Number of songs: {}".format(len(rnd_items)))

        self._clean_target_path(training)
        self._copy_items_to_target(training, rnd_items)
        # done.?

    def _clean_target_path(self, training: Subview):
        if self.config["clean_target"].get():
            target_path = self._get_target_path(training)
            self._say("Cleaning target: {}".format(target_path))

            # @todo: Should only clean song files
            song_extensions = ["mp3", "mp4", "flac", "wav"]
            target_file_list = []
            for ext in song_extensions:
                target_file_list += glob(os.path.join(target_path, "*.{}".format(ext)))

            for f in target_file_list:
                log.debug("DEL: {}".format(f))
                os.remove(f)

    def _copy_items_to_target(self, training: Subview, rnd_items):
        target_path = self._get_target_path(training)
        self._say("Copying to target path: {}".format(target_path))

        def random_string(length=6):
            letters = string.ascii_letters + string.digits
            return ''.join(random.choice(letters) for i in range(length))

        cnt = 0
        for item in rnd_items:
            src = os.path.realpath(item.get("path").decode("utf-8"))
            fn, ext = os.path.splitext(src)
            gen_filename = "{0}_{1}{2}".format(str(cnt).zfill(6), random_string(), ext)
            dst = "{0}/{1}".format(target_path, gen_filename)
            log.debug("Copying[{1}]: {0}".format(src, gen_filename))
            copyfile(src, dst)
            cnt += 1

    def _get_target_path(self, training: Subview):
        target_path = ""
        target_name = self._get_config_value_bubble_up(training, "target")
        targets = self.config["targets"].get()
        log.debug("Selected target name: {0}".format(target_name))
        if target_name in targets:
            target_path = os.path.realpath(Path(targets.get(target_name)).expanduser())
            log.debug("Selected target path: {0}".format(target_path))

        return target_path

    @staticmethod
    def _get_randomized_items(items, duration_min):
        """ This randomization and limiting to duration_min is very basic
        @todo: after randomization select songs to be as cose as possible to the duration_min (+-5seconds)
        """
        r_limit = 1
        r_time_minutes = duration_min
        r_equal_chance = True
        rnd_items = random_objs(list(items), False, r_limit, r_time_minutes, r_equal_chance)

        return rnd_items

    def _retrieve_library_items(self, training: Subview):
        query = []

        # Filter command line queries
        reserved_fields = ["bpm", "length"]
        while self.query:
            el = self.query.pop(0)
            el_ok = True
            for reserved_field in reserved_fields:
                reserved_field = reserved_field + ":"
                if reserved_field == el[:len(reserved_field)]:
                    el_ok = False
            if el_ok:
                query.append(el)
            else:
                log.debug("removing reserved filter: {}".format(el))

        # Add BPM query
        song_bpm = self._get_config_value_bubble_up(training, "song_bpm")
        query_element = "bpm:{0}..{1}".format(song_bpm[0], song_bpm[1])
        query.append(query_element)

        # Add Length query
        song_len = self._get_config_value_bubble_up(training, "song_len")
        query_element = "length:{0}..{1}".format(song_len[0], song_len[1])
        query.append(query_element)

        log.debug("final song selection query: {}".format(query))

        items = self.lib.items(query)

        return items

    @staticmethod
    def _get_duration_of_items(items):
        """
        Calculate the total duration of the items
        :param items: list
        :return: int
        """
        total_time = 0
        for item in items:
            total_time += int(item.get("length"))

        return total_time

    def list_trainings(self):
        """
        # @todo: order keys
        :return: void
        """
        if "trainings" not in self.config:
            self._say("You have not created any trainings yet.")
            return

        self._say("Available trainings:")
        training_names = list(self.config["trainings"].keys())
        for training_name in training_names:
            self.list_training_attributes(training_name)

    def list_training_attributes(self, training_name: str):
        """
        @todo: Explain keys
        @todo: target is a special case and the value from targets should also be shown
        :param training_name:
        :return: void
        """
        target: Subview = self.config["trainings"][training_name]
        try:
            training_keys = target.keys()
            self._say("{0} ::: {1}".format("=" * 40, training_name))
            training_keys = list(set(DEFAULT_TRAINING_KEYS) | set(training_keys))
            training_keys.sort()
            for tkey in training_keys:
                tval = self._get_config_value_bubble_up(target, tkey)
                self._say("{0} : {1}".format(tkey, tval))
        except ConfigTypeError:
            pass

    @staticmethod
    def _get_config_value_bubble_up(target: Subview, attrib: str):
        """
        Method that will bubble up in the configuration hierarchy to find the attribute
        """
        value = None
        found = False

        while not found:
            odict: OrderedDict = target.flatten()
            if attrib in odict:
                value = odict.get(attrib)
                found = True
            else:
                if target.root() != target.parent:
                    target: Subview = target.parent
                else:
                    # self._say("No more levels!")
                    found = True

        return value

    def _say(self, msg):
        if not self.quiet:
            log.info(msg)
        else:
            log.debug(msg)
