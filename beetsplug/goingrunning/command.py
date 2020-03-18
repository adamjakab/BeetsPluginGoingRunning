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
from beets.dbcore.queryparse import parse_query_part
from beets.library import Library, Item, parse_query_string
from beets.ui import Subcommand, decargs
from beets.util.confit import Subview, NotFoundError

from beetsplug.goingrunning import common as GRC

# The plugin
__PLUGIN_NAME__ = u'goingrunning'
__PLUGIN_SHORT_NAME__ = u'run'
__PLUGIN_SHORT_DESCRIPTION__ = u'run with the music that matches your training sessions'


class GoingRunningCommand(Subcommand):
    log = None
    config: Subview = None
    lib: Library = None
    query = None
    parser: OptionParser = None

    cfg_quiet = False
    cfg_count = False
    cfg_dry_run = False

    def __init__(self, cfg):
        self.config = cfg
        self.log = GRC.get_beets_logger()

        self.parser = OptionParser(usage='beet goingrunning [training] [options] [QUERY...]')

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

        self.parser.add_option(
            '-q', '--cfg_quiet',
            action='store_true', dest='quiet', default=False,
            help=u'keep cfg_quiet'
        )

        self.parser.add_option(
            '-v', '--version',
            action='store_true', dest='version', default=False,
            help=u'show plugin version'
        )

        # Keep this at the end
        super(GoingRunningCommand, self).__init__(
            parser=self.parser,
            name=__PLUGIN_NAME__,
            help=__PLUGIN_SHORT_DESCRIPTION__,
            aliases=[__PLUGIN_SHORT_NAME__]
        )

    def func(self, lib: Library, options, arguments):
        self.cfg_quiet = options.quiet
        self.cfg_count = options.count
        self.cfg_dry_run = options.dry_run

        self.lib = lib
        self.query = decargs(arguments)

        # TEMPORARY: Verify configuration upgrade!
        # There is a major backward incompatible upgrade in version 1.1.1
        try:
            self.verify_configuration_upgrade()
        except RuntimeError as e:
            self._say("*" * 80)
            self._say("********************   INCOMPATIBLE PLUGIN CONFIGURATION   *********************")
            self._say("*" * 80)
            self._say("* Your configuration has been created for an older version of the plugin.")
            self._say("* Since version 1.1.1 the plugin has implemented changes that require your "
                      "current configuration to be updated.")
            self._say("* Please read the updated documentation here and update your configuration.")
            self._say(
                "* Documentation: https://github.com/adamjakab/BeetsPluginGoingRunning/blob/master/README.md"
                "#configuration")
            self._say("* I promise it will not happen again ;)")
            self._say("* " + str(e))
            self._say("* The plugin will exit now.")
            self._say("*" * 80)
            return

        # You must either pass a training name or request listing
        if len(self.query) < 1 and not (options.list or options.version):
            self.log.warning(
                "You can either pass the name of a training or request a "
                "listing (--list)!")
            self.parser.print_help()
            return

        if options.version:
            self.show_version_information()
            return
        elif options.list:
            self.list_trainings()
            return

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
        if self.cfg_count:
            self._say("Number of songs available: {}".format(len(lib_items)))
            return

        self._say("Handling training: {0}".format(training_name))

        # Check count
        if len(lib_items) < 1:
            self._say(
                "There are no songs in your library that match this training!")
            return

        # Verify target device path path
        if not self._get_destination_path_for_training(training):
            return

        # 1) order items by scoring system (need ordering in config)
        GRC.score_library_items(training, lib_items)
        sorted_lib_items = sorted(lib_items, key=operator.attrgetter('ordering_score'))

        # 2) select random items n from the ordered list(T=length) - by
        # chosing n times song from the remaining songs between 1 and m
        # where m = T/n
        duration = GRC.get_training_attribute(training, "duration")
        # sel_items = GRC.get_randomized_items(lib_items, duration)
        sel_items = self._get_items_for_duration(sorted_lib_items, duration)

        total_time = GRC.get_duration_of_items(sel_items)
        # @todo: check if total time is close to duration - (config might be
        #  too restrictive or too few songs)

        # Show some info
        self._say("Available songs: {}".format(len(lib_items)))
        self._say("Selected songs: {}".format(len(sel_items)))
        self._say("Planned training duration: {0}".format(GRC.get_human_readable_time(duration * 60)))
        self._say("Total song duration: {}".format(GRC.get_human_readable_time(total_time)))

        # Show the selected songs and exit
        flds = ["bpm", "year", "length", "artist", "title"]
        self.display_library_items(sel_items, flds, prefix="Selected: ")

        # todo: move this inside the nex methods to show what would be done
        if self.cfg_dry_run:
            return

        self._clean_target_path(training)
        self._copy_items_to_target(training, sel_items)
        self._say("Run!")

    def _clean_target_path(self, training: Subview):
        target_name = GRC.get_training_attribute(training, "target")

        if self._get_target_attribute_for_training(training, "clean_target"):
            dst_path = self._get_destination_path_for_training(training)

            self._say("Cleaning target[{0}]: {1}".format(target_name, dst_path))
            song_extensions = ["mp3", "mp4", "flac", "wav", "ogg", "wma", "m3u"]
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
        target_name = GRC.get_training_attribute(training, "target")
        dst_path = self._get_destination_path_for_training(training)
        self._say("Copying to target[{0}]: {1}".format(target_name, dst_path))

        def random_string(length=6):
            letters = string.ascii_letters + string.digits
            return ''.join(random.choice(letters) for i in range(length))

        cnt = 0
        for item in rnd_items:
            src = os.path.realpath(item.get("path").decode("utf-8"))
            if not os.path.isfile(src):
                # todo: this is bad enough to interrupt! create option for this
                self.log.warning("File does not exist: {}".format(src))
                continue

            fn, ext = os.path.splitext(src)
            gen_filename = "{0}_{1}{2}".format(str(cnt).zfill(6),
                                               random_string(), ext)
            dst = "{0}/{1}".format(dst_path, gen_filename)
            self.log.debug("Copying[{1}]: {0}".format(src, gen_filename))
            copyfile(src, dst)
            cnt += 1

    def _get_target_for_training(self, training: Subview):
        target_name = GRC.get_training_attribute(training, "target")
        self.log.debug("Finding target: {0}".format(target_name))

        if not self.config["targets"][target_name].exists():
            self._say("The target name[{0}] is not defined!".format(target_name))
            return

        return self.config["targets"][target_name]

    def _get_target_attribute_for_training(self, training: Subview, attrib: str = "name"):
        target_name = GRC.get_training_attribute(training, "target")
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
            attrib_val = GRC.get_target_attribute(target, attrib)

        self.log.debug(
            "Found target[{0}] attribute[{1}] path: {2}".format(target_name, attrib, attrib_val))

        return attrib_val

    def _get_destination_path_for_training(self, training: Subview):
        target_name = GRC.get_training_attribute(training, "target")
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
        _min, _max, _sum, _avg = GRC.get_min_max_sum_avg_for_items(items, "length")

        if _avg > 0:
            est_num_songs = round(duration * 60 / _avg)
        else:
            est_num_songs = 0

        if est_num_songs > 0:
            bin_size = len(items) / est_num_songs
        else:
            bin_size = 0

        self.log.debug("Estimated number of songs: {}".format(est_num_songs))
        self.log.debug("Bin Size: {}".format(bin_size))

        for i in range(0, est_num_songs):
            bin_start = round(i * bin_size)
            bin_end = round(bin_start + bin_size)
            song_index = random.randint(bin_start, bin_end)
            try:
                selected.append(items[song_index])
            except IndexError:
                pass

        return selected

    def _gather_query_elements(self, training: Subview):
        """Order(strongest to weakest): command -> training -> flavours
        """
        command_query = self.query
        training_query = []
        flavour_query = []

        # Append the query elements from the configuration
        tconf = GRC.get_training_attribute(training, "query")
        if tconf:
            for key in tconf.keys():
                training_query.append(GRC.get_beet_query_formatted_string(key, tconf.get(key)))

        # Append the query elements from the flavours defined on the training
        flavours = GRC.get_training_attribute(training, "use_flavours")
        if flavours:
            flavours = [flavours] if type(flavours) == str else flavours
            for flavour_name in flavours:
                flavour: Subview = self.config["flavours"][flavour_name]
                flavour_query += GRC.get_flavour_elements(flavour)

        self.log.debug("Command query elements: {}".format(command_query))
        self.log.debug("Training query elements: {}".format(training_query))
        self.log.debug("Flavour query elements: {}".format(flavour_query))

        raw_combined_query = command_query + training_query + flavour_query
        self.log.debug("Raw combined query elements: {}".format(raw_combined_query))

        # Remove duplicate keys
        combined_query = []
        used_keys = []
        for query_part in raw_combined_query:
            key = parse_query_part(query_part)[0]
            if key not in used_keys:
                used_keys.append(key)
                combined_query.append(query_part)

        self.log.debug("Clean combined query elements: {}".format(combined_query))

        return combined_query

    def _retrieve_library_items(self, training: Subview):
        full_query = self._gather_query_elements(training)
        parsed_query = parse_query_string(" ".join(full_query), Item)[0]
        self.log.debug("Song selection query: {}".format(parsed_query))

        return self.lib.items(parsed_query)

    def display_library_items(self, items, fields, prefix=""):
        fmt = prefix
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
        """
        if not self.config["trainings"].exists() or len(self.config["trainings"].keys()) == 0:
            self._say("You have not created any trainings yet.")
            return

        self._say("Available trainings:")
        trainings = list(self.config["trainings"].keys())
        training_names = [s for s in trainings if s != "fallback"]
        for training_name in training_names:
            self.list_training_attributes(training_name)

    def list_training_attributes(self, training_name: str):
        if not self.config["trainings"].exists() or not self.config["trainings"][training_name].exists():
            self.log.debug("Training[{0}] does not exist.".format(training_name))
            return

        training: Subview = self.config["trainings"][training_name]
        training_keys = training.keys()
        self._say("{0} ::: {1}".format("=" * 40, training_name))

        training_keys = list(set(GRC.MUST_HAVE_TRAINING_KEYS) | set(training_keys))
        training_keys.sort()

        for tkey in training_keys:
            tval = GRC.get_training_attribute(training, tkey)
            if isinstance(tval, dict):
                value = []
                for k in tval:
                    value.append("{key}({val})".format(key=k, val=tval[k]))
                tval = ", ".join(value)

            self._say("{0}: {1}".format(tkey, tval))

    def show_version_information(self):
        from beetsplug.goingrunning.version import __version__
        self._say("Goingrunning(beets-{}) plugin for Beets: v{}".format(__PLUGIN_NAME__, __version__))

    def verify_configuration_upgrade(self):
        """Check if user has old(pre v1.1.1) configuration keys in config
        """
        trainings = list(self.config["trainings"].keys())
        training_names = [s for s in trainings if s != "fallback"]
        for training_name in training_names:
            training: Subview = self.config["trainings"][training_name]
            tkeys = training.keys()
            for tkey in tkeys:
                if tkey in ["song_bpm", "song_len"]:
                    raise RuntimeError("Offending key in training({}): {}".format(training_name, tkey))

    def _say(self, msg):
        """Log and print to stdout
        """
        self.log.debug(msg)
        if not self.cfg_quiet:
            print(msg)
