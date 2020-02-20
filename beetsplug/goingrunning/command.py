#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 11:32 AM
#  License: See LICENSE.txt
#

import random
import os
import string
from optparse import OptionParser
from pathlib import Path

from shutil import copyfile
from glob import glob
from beets.dbcore.db import Results
from beets.library import Library as BeatsLibrary, Item
from beets.ui import Subcommand, decargs
from beets.util.confit import Subview, NotFoundError

from beetsplug.goingrunning import common as GRC


class GoingRunningCommand(Subcommand):
    log = None
    config: Subview = None
    lib = None
    query = None
    parser = None

    quiet = False
    count_only = False

    def __init__(self, cfg):
        self.config = cfg
        self.log = GRC.get_beets_logger()

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
            self.log.warning("You can either pass the name of a training or request a listing (--list)!")
            self.parser.print_help()
            return

        if options.list:
            self.list_trainings()
        else:
            self.handle_training()

    def handle_training(self):
        training_name = self.query.pop(0)

        training: Subview = self.config["trainings"][training_name]
        if not training.exists():
            self._say("There is no training[{0}] registered with this name!".format(training_name))
            return

        # Get the library items
        lib_items: Results = self._retrieve_library_items(training)

        # Show count only
        if self.count_only:
            self._say("Number of songs: {}".format(len(lib_items)))
            return

        self._say("Handling training: {0}".format(training_name))

        # Check count
        if len(lib_items) < 1:
            self._say("There are no songs in your library that match this training!")
            return

        # Get randomized items
        duration = GRC.get_config_value_bubble_up(training, "duration")
        rnd_items = GRC.get_randomized_items(lib_items, duration)
        total_time = GRC.get_duration_of_items(rnd_items)
        # @todo: check if total time is close to duration - (config might be too restrictive or too few songs)

        # Verify target path
        target_path = self._get_target_path(training)
        if not target_path:
            return

        # Show some info
        self._say("Training duration: {0}".format(GRC.get_human_readable_time(duration * 60)))
        self._say("Total song duration: {}".format(GRC.get_human_readable_time(total_time)))
        self._say("Number of songs available: {}".format(len(lib_items)))
        self._say("Number of songs selected: {}".format(len(rnd_items)))

        self._clean_target_path(training)
        self._copy_items_to_target(training, rnd_items)
        self._say("Run!")

    def _clean_target_path(self, training: Subview):
        if GRC.get_config_value_bubble_up(training, "clean_target"):
            target_path = self._get_target_path(training)
            self._say("Cleaning target[{0}]: {1}".format(training["target"].get(), target_path))

            song_extensions = ["mp3", "mp4", "flac", "wav"]
            target_file_list = []
            for ext in song_extensions:
                target_file_list += glob(os.path.join(target_path, "*.{}".format(ext)))

            for f in target_file_list:
                self.log.debug("Deleting: {}".format(f))
                os.remove(f)

    def _copy_items_to_target(self, training: Subview, rnd_items):
        target_path = self._get_target_path(training)
        self._say("Copying to target[{0}]: {1}".format(training["target"].get(), target_path))

        def random_string(length=6):
            letters = string.ascii_letters + string.digits
            return ''.join(random.choice(letters) for i in range(length))

        cnt = 0
        for item in rnd_items:
            src = os.path.realpath(item.get("path").decode("utf-8"))
            fn, ext = os.path.splitext(src)
            gen_filename = "{0}_{1}{2}".format(str(cnt).zfill(6), random_string(), ext)
            dst = "{0}/{1}".format(target_path, gen_filename)
            self.log.debug("Copying[{1}]: {0}".format(src, gen_filename))
            copyfile(src, dst)
            cnt += 1

    def _get_target_path(self, training: Subview):
        target_name = GRC.get_config_value_bubble_up(training, "target")
        targets = self.config["targets"].get()
        self.log.debug("Checking target name: {0}".format(target_name))

        if target_name not in targets.keys():
            self._say("The target name[{0}] is not defined!".format(target_name))
            return

        target_path = os.path.realpath(Path(targets.get(target_name)).expanduser())
        self.log.debug("Found target path: {0}".format(target_path))

        if not os.path.isdir(target_path):
            self._say("The target[{0}] path does not exist: {1}".format(target_name, target_path))
            return

        return target_path

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
                self.log.debug("removing reserved filter: {}".format(el))

        # Add BPM query
        song_bpm = GRC.get_config_value_bubble_up(training, "song_bpm")
        query_element = "bpm:{0}..{1}".format(song_bpm[0], song_bpm[1])
        query.append(query_element)

        # Add Length query
        song_len = GRC.get_config_value_bubble_up(training, "song_len")
        query_element = "length:{0}..{1}".format(song_len[0], song_len[1])
        query.append(query_element)

        self.log.debug("final song selection query: {}".format(query))

        items = self.lib.items(query)

        return items

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
        if target.exists() and isinstance(target.get(), dict):
            training_keys = target.keys()
            self._say("{0} ::: {1}".format("=" * 40, training_name))
            training_keys = list(set(GRC.MUST_HAVE_TRAINING_KEYS) | set(training_keys))
            training_keys.sort()
            for tkey in training_keys:
                tval = GRC.get_config_value_bubble_up(target, tkey)
                self._say("{0}: {1}".format(tkey, tval))
        else:
            self._say("Training[{0}] does not exist.".format(training_name))

    def _say(self, msg):
        self.log.debug(msg)
        if not self.quiet:
            print(msg)
