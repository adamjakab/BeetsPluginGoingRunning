#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 11:32 AM
#  License: See LICENSE.txt
#

import operator
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

# from beets.dbcore.types import Integer, Float
# import pandas as pd

from beetsplug.goingrunning import common as GRC


class GoingRunningCommand(Subcommand):
    log = None
    config: Subview = None
    lib = None
    query = None
    parser = None

    quiet = False
    count_only = False
    dry_run = False

    def __init__(self, cfg):
        self.config = cfg
        self.log = GRC.get_beets_logger()

        self.parser = OptionParser(usage='%prog training [options] [QUERY...]')

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

        self.parser.add_option(
            '-d', '--dry-run',
            action='store_true', dest='dry_run', default=False,
            help=u'Do not delete/copy any songs. Just show what would be done'
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
        self.dry_run = options.dry_run

        self.lib = lib
        self.query = decargs(arguments)

        # You must either pass a training name or request listing
        if len(self.query) < 1 and not options.list:
            self.log.warning(
                "You can either pass the name of a training or request a "
                "listing (--list)!")
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
            self._say(
                "There is no training[{0}] registered with this name!".format(
                    training_name))
            return

        # Get the library items
        lib_items: Results = self._retrieve_library_items(training)

        # Show count only
        if self.count_only:
            self._say("Number of songs available: {}".format(len(lib_items)))
            return

        self._say("Handling training: {0}".format(training_name))

        # Check count
        if len(lib_items) < 1:
            self._say(
                "There are no songs in your library that match this training!")
            return

        # 1) order items by scoring system (need ordering in config)
        self._score_library_items(training, lib_items)
        sorted_lib_items = sorted(lib_items,
                                  key=operator.attrgetter('ordering_score'))

        # 2) select random items n from the ordered list(T=length) - by
        # chosing n times song from the remaining songs between 1 and m
        # where m = T/n
        duration = GRC.get_config_value_bubble_up(training, "duration")
        # sel_items = GRC.get_randomized_items(lib_items, duration)
        sel_items = self._get_items_for_duration(sorted_lib_items, duration)

        total_time = GRC.get_duration_of_items(sel_items)
        # @todo: check if total time is close to duration - (config might be
        #  too restrictive or too few songs)

        # Verify target device path path
        if not self._get_destination_path_for_training(training):
            return

        # Show some info
        self._say("Training duration: {0}".format(
            GRC.get_human_readable_time(duration * 60)))
        self._say("Selected song duration: {}".format(
            GRC.get_human_readable_time(total_time)))
        self._say("Number of songs available: {}".format(len(lib_items)))
        self._say("Number of songs selected: {}".format(len(sel_items)))

        # Show the selected songs and exit
        # flds = ("ordering_score", "bpm", "year", "length", "ordering_info",
        # "artist", "title")
        flds = ("bpm", "year", "length", "artist", "title")
        # self.display_library_items(sorted_lib_items, flds)
        # self._say("="*80)
        self.display_library_items(sel_items, flds)

        # todo: move this inside the nex methods to show what would be done
        if self.dry_run:
            return

        self._clean_target_path(training)
        self._copy_items_to_target(training, sel_items)
        self._say("Run!")

    def _clean_target_path(self, training: Subview):
        target_name = GRC.get_config_value_bubble_up(training, "target")

        if self._get_target_attribute_for_training(training, "clean_target"):
            dst_path = self._get_destination_path_for_training(training)

            self._say("Cleaning target[{0}]: {1}".format(target_name, dst_path))
            song_extensions = ["mp3", "mp4", "flac", "wav"]
            target_file_list = []
            for ext in song_extensions:
                target_file_list += glob(
                    os.path.join(dst_path, "*.{}".format(ext)))

            for f in target_file_list:
                self.log.debug("Deleting: {}".format(f))
                os.remove(f)

        additional_files = self._get_target_attribute_for_training(training,
                                                                   "delete_from_device")
        if additional_files and len(additional_files) > 0:
            root = self._get_target_attribute_for_training(training,
                                                           "device_root")
            root = Path(root).expanduser()

            self._say("Deleting additional files: {0}".format(additional_files))

            for path in additional_files:
                path = Path(str.strip(path, "/"))
                dst_path = os.path.realpath(root.joinpath(path))

                if not os.path.isfile(dst_path):
                    self.log.debug(
                        "The file to delete does not exist: {0}".format(path))
                    continue

                self.log.debug("Deleting: {}".format(dst_path))
                os.remove(dst_path)

    def _copy_items_to_target(self, training: Subview, rnd_items):
        target_name = GRC.get_config_value_bubble_up(training, "target")
        dst_path = self._get_destination_path_for_training(training)
        self._say("Copying to target[{0}]: {1}".format(target_name, dst_path))

        def random_string(length=6):
            letters = string.ascii_letters + string.digits
            return ''.join(random.choice(letters) for i in range(length))

        cnt = 0
        for item in rnd_items:
            src = os.path.realpath(item.get("path").decode("utf-8"))
            fn, ext = os.path.splitext(src)
            gen_filename = "{0}_{1}{2}".format(str(cnt).zfill(6),
                                               random_string(), ext)
            dst = "{0}/{1}".format(dst_path, gen_filename)
            self.log.debug("Copying[{1}]: {0}".format(src, gen_filename))
            copyfile(src, dst)
            cnt += 1

    def _get_target_for_training(self, training: Subview):
        target_name = GRC.get_config_value_bubble_up(training, "target")
        self.log.debug("Finding target: {0}".format(target_name))
        target: Subview = self.config["targets"][target_name]

        if not target.exists():
            self._say(
                "The target name[{0}] is not defined!".format(target_name))
            return

        return target

    def _get_target_attribute_for_training(self, training: Subview,
                                           attrib: str = "name"):
        target_name = GRC.get_config_value_bubble_up(training, "target")
        self.log.debug("Getting attribute[{0}] for target: {1}".format(attrib,
                                                                       target_name))
        target = self._get_target_for_training(training)
        if not target:
            return

        if attrib == "name":
            attrib_val = target_name
        if attrib in ("device_root", "device_path", "delete_from_device"):
            # these should NOT propagate up
            try:
                attrib_val = target[attrib].get()
            except NotFoundError:
                attrib_val = None
        else:
            attrib_val = GRC.get_config_value_bubble_up(target, attrib)

        self.log.debug(
            "Found target[{0}] attribute[{1}] path: {2}".format(target_name,
                                                                attrib,
                                                                attrib_val))

        return attrib_val

    def _get_destination_path_for_training(self, training: Subview):
        target_name = GRC.get_config_value_bubble_up(training, "target")
        root = self._get_target_attribute_for_training(training, "device_root")
        path = self._get_target_attribute_for_training(training, "device_path")
        path = path or ""

        if not root:
            self._say(
                "The target[{0}] does not declare a device root path.".format(
                    target_name))
            return

        root = Path(root).expanduser()
        path = Path(str.strip(path, "/"))
        dst_path = os.path.realpath(root.joinpath(path))

        if not os.path.isdir(dst_path):
            self._say(
                "The target[{0}] path does not exist: {1}".format(target_name,
                                                                  dst_path))
            return

        self.log.debug(
            "Found target[{0}] path: {0}".format(target_name, dst_path))

        return dst_path

    def _get_items_for_duration(self, items, duration):
        selected = []
        total_time = 0
        _min, _max, _sum, _avg = self._get_min_max_sum_avg_for_items(items,
                                                                     "length")
        est_num_songs = round(duration * 60 / _avg)
        bin_size = len(items) / est_num_songs

        self._say("Estimated number of songs: {}".format(est_num_songs))
        self._say("Bin Size: {}".format(bin_size))

        for i in range(0, est_num_songs):
            bin_start = round(i * bin_size)
            bin_end = round(bin_start + bin_size)
            song_index = random.randint(bin_start, bin_end)
            try:
                selected.append(items[song_index])
            except IndexError:
                pass

        return selected

    def _get_min_max_sum_avg_for_items(self, items, field_name):
        _min = 99999999.9
        _max = 0
        _sum = 0
        _avg = 0
        for item in items:
            item: Item
            try:
                field_value = round(float(item.get(field_name, None)), 3)
            except ValueError:
                field_value = None
            except TypeError:
                field_value = None

            # Min
            if field_value is not None and field_value < _min:
                _min = field_value

            # Max
            if field_value is not None and field_value > _max:
                _max = field_value

            # Sum
            if field_value is not None:
                _sum = _sum + field_value

        # Avg
        _avg = round(_sum / len(items), 3)

        return _min, _max, _sum, _avg

    def _score_library_items(self, training: Subview, items):
        ordering = {}
        fields = []
        if training["ordering"].exists() and len(
                training["ordering"].keys()) > 0:
            ordering = training["ordering"].get()
            fields = list(ordering.keys())

        default_field_data = {
            "min": 99999999.9,
            "max": 0.0,
            "delta": 0.0,
            "step": 0.0,
            "direction": "+",
            "weight": 100
        }

        # Build Order Info
        order_info = {}
        for field in fields:
            field_name = field.strip("+-")
            field_direction = field.strip(field_name)
            order_info[field_name] = default_field_data.copy()
            order_info[field_name]["direction"] = field_direction
            order_info[field_name]["weight"] = ordering[field]

        # self._say("ORDER INFO #1: {0}".format(order_info))

        # Populate Order Info
        for field_name in order_info.keys():
            field_data = order_info[field_name]
            _min, _max, _sum, _avg = self._get_min_max_sum_avg_for_items(items,
                                                                         field_name)
            field_data["min"] = _min
            field_data["max"] = _max

        # self._say("ORDER INFO #2: {0}".format(order_info))

        # todo: this will not work anymore - find a better way
        # Remove bad items from Order Info
        # bad_oi = [field for field in order_info if
        #           order_info[field]["min"] == default_field_data["min"] and
        #           order_info[field]["max"] == default_field_data["max"]
        #           ]
        # for field in bad_oi: del order_info[field]

        # self._say("ORDER INFO #3: {0}".format(order_info))

        # Calculate other values in Order Info
        for field_name in order_info.keys():
            field_data = order_info[field_name]
            field_data["delta"] = field_data["max"] - field_data["min"]
            field_data["step"] = round(100 / field_data["delta"], 3)

        # self._say("ORDER INFO: {0}".format(order_info))
        # {'bpm': {'min': 90.0, 'max': 99.0, 'delta': 9.0, 'step': 11.111,
        # 'direction': '+', 'weight': 88}, ...

        # Score the library items
        for item in items:
            item: Item
            item["ordering_score"] = 0
            item["ordering_info"] = {}
            for field_name in order_info.keys():
                field_data = order_info[field_name]
                try:
                    field_value = round(float(item.get(field_name, None)), 3)
                except ValueError:
                    field_value = None
                except TypeError:
                    field_value = None

                if field_value is None:
                    # Make up average value
                    field_value = round(field_data["delta"] / 2, 3)

                distance_from_min = round(field_value - field_data["min"], 3)

                # This is linear (we could some day use different models)
                # field_score should always be between 0 and 100
                field_score = round(distance_from_min * field_data["step"], 3)
                field_score = field_score if field_score > 0 else 0
                field_score = field_score if field_score < 100 else 100

                weighted_field_score = round(
                    field_data["weight"] * field_score / 100, 3)
                if field_data["direction"] == "-":
                    weighted_field_score *= -1

                item["ordering_score"] = round(
                    item["ordering_score"] + weighted_field_score, 3)

                item["ordering_info"][field_name] = {
                    "dist": distance_from_min,
                    "fld_score": field_score,
                    "wfld_score": weighted_field_score
                }

    def _retrieve_library_items(self, training: Subview):
        """Return all items that match the query defined on the training and
        additionally on the command line
        """
        query_items = {}

        # Query defined by the training
        # USE: GRC.get_config_value_bubble_up(training, "query")
        if training["query"].exists() and len(training["query"].keys()) > 0:
            training_query = training["query"].get()
            for tq in training_query.keys():
                query_items[tq] = training_query[tq]

        # Query passed on command line
        while self.query:
            qel: str = self.query.pop(0)
            qk, qv = qel.split(":", maxsplit=1)
            query_items[qk] = qv

        query = []
        for tq in query_items:
            query.append("{0}:{1}".format(tq, query_items[tq]))

        self.log.debug("Song selection query: {}".format(query))

        return self.lib.items(query)

    def display_library_items(self, items, fields):
        fmt = ""
        for field in fields:
            fmt += "[{0}:{{{0}}}]".format(field)

        for item in items:
            kwargs = {}
            for field in fields:
                fld_val = None
                if hasattr(item, field):
                    fld_val = item[field]

                kwargs[field] = fld_val
            try:
                self._say(fmt.format(**kwargs))
            except IndexError:
                pass

    def list_trainings(self):
        """
        # @todo: order keys
        :return: void
        """
        if not self.config["trainings"].exists() or len(
                self.config["trainings"].keys()) == 0:
            self._say("You have not created any trainings yet.")
            return

        self._say("Available trainings:")
        training_names = list(self.config["trainings"].keys())
        for training_name in training_names:
            self.list_training_attributes(training_name)

    def list_training_attributes(self, training_name: str):
        """
        @todo: Explain keys
        @todo: "target" is a special case and the value from targets (paths)
        should also be shown
        :param training_name:
        :return: void
        """
        target: Subview = self.config["trainings"][training_name]
        if target.exists() and isinstance(target.get(), dict):
            training_keys = target.keys()
            self._say("{0} ::: {1}".format("=" * 40, training_name))
            training_keys = list(
                set(GRC.MUST_HAVE_TRAINING_KEYS) | set(training_keys))
            training_keys.sort()
            for tkey in training_keys:
                tval = GRC.get_config_value_bubble_up(target, tkey)
                self._say("{0}: {1}".format(tkey, tval))
        # else:
        #     self.log.debug("Training[{0}] does not exist.".format(training_name))

    def _say(self, msg):
        self.log.debug(msg)
        if not self.quiet:
            print(msg)
