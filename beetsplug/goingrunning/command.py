#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 11:32 AM
#  License: See LICENSE.txt
#

import operator
import os
import random
import string
from glob import glob
from optparse import OptionParser
from pathlib import Path
from shutil import copyfile

from beets import library
from beets.dbcore.db import Results
from beets.dbcore.queryparse import parse_query_part
from beets.library import Library, Item, parse_query_string
from beets.ui import Subcommand, decargs
from beets.util.confit import Subview, NotFoundError

from beetsplug.goingrunning import common

# The plugin
__PLUGIN_NAME__ = u'goingrunning'
__PLUGIN_SHORT_NAME__ = u'run'
__PLUGIN_SHORT_DESCRIPTION__ = u'run with the music that matches your training sessions'


class GoingRunningCommand(Subcommand):
    config: Subview = None
    lib: Library = None
    query = None
    parser: OptionParser = None

    cfg_quiet = False
    cfg_count = False
    cfg_dry_run = False

    def __init__(self, cfg):
        self.config = cfg

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
            common.say("*" * 80)
            return

        # You must either pass a training name or request listing
        if len(self.query) < 1 and not (options.list or options.version):
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
        common.score_library_items(training, lib_items)
        sorted_lib_items = sorted(lib_items, key=operator.attrgetter('ordering_score'))

        # 2) select random items n from the ordered list(T=length) - by
        # chosing n times song from the remaining songs between 1 and m
        # where m = T/n
        duration = common.get_training_attribute(training, "duration")
        # sel_items = common.get_randomized_items(lib_items, duration)
        sel_items = self._get_items_for_duration(sorted_lib_items, duration)

        total_time = common.get_duration_of_items(sel_items)
        # @todo: check if total time is close to duration - (config might be
        #  too restrictive or too few songs)

        # Show some info
        self._say("Available songs: {}".format(len(lib_items)))
        self._say("Selected songs: {}".format(len(sel_items)))
        self._say("Planned training duration: {0}".format(common.get_human_readable_time(duration * 60)))
        self._say("Total song duration: {}".format(common.get_human_readable_time(total_time)))

        # Show the selected songs
        flds = self._get_training_query_element_keys(training)
        flds += ["artist", "title"]
        self.display_library_items(sel_items, flds, prefix="Selected: ")

        # todo: move this inside the nex methods to show what would be done
        if self.cfg_dry_run:
            return

        self._clean_target_path(training)
        self._copy_items_to_target(training, sel_items)
        self._say("Run!")

    def _clean_target_path(self, training: Subview):
        target_name = common.get_training_attribute(training, "target")

        if self._get_target_attribute_for_training(training, "clean_target"):
            dst_path = self._get_destination_path_for_training(training)

            self._say("Cleaning target[{0}]: {1}".format(target_name, dst_path))
            song_extensions = ["mp3", "mp4", "flac", "wav", "ogg", "wma", "m3u"]
            target_file_list = []
            for ext in song_extensions:
                target_file_list += glob(
                    os.path.join(dst_path, "*.{}".format(ext)))

            for f in target_file_list:
                self._say("Deleting: {}".format(f), log_only=True)
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
                    self._say("The file to delete does not exist: {0}".format(path), log_only=True)
                    continue

                self._say("Deleting: {}".format(dst_path), log_only=True)
                os.remove(dst_path)

    def _copy_items_to_target(self, training: Subview, rnd_items):
        target_name = common.get_training_attribute(training, "target")
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
                self._say("File does not exist: {}".format(src))
                continue

            fn, ext = os.path.splitext(src)
            gen_filename = "{0}_{1}{2}".format(str(cnt).zfill(6),
                                               random_string(), ext)
            dst = "{0}/{1}".format(dst_path, gen_filename)
            self._say("Copying[{1}]: {0}".format(src, gen_filename), log_only=True)
            copyfile(src, dst)
            cnt += 1

    def _get_target_for_training(self, training: Subview):
        target_name = common.get_training_attribute(training, "target")
        self._say("Finding target: {0}".format(target_name), log_only=True)

        if not self.config["targets"][target_name].exists():
            self._say("The target name[{0}] is not defined!".format(target_name))
            return

        return self.config["targets"][target_name]

    def _get_target_attribute_for_training(self, training: Subview, attrib: str = "name"):
        target_name = common.get_training_attribute(training, "target")
        self._say("Getting attribute[{0}] for target: {1}".format(attrib,
                                                                  target_name), log_only=True)
        target = self._get_target_for_training(training)
        if not target:
            return

        if attrib == "name":
            attrib_val = target_name
        elif attrib in ("device_root", "device_path", "delete_from_device"):
            # these should NOT propagate up
            try:
                attrib_val = target[attrib].get()
            except NotFoundError:
                attrib_val = None
        else:
            attrib_val = common.get_target_attribute(target, attrib)

        self._say(
            "Found target[{0}] attribute[{1}] path: {2}".format(target_name, attrib, attrib_val), log_only=True)

        return attrib_val

    def _get_destination_path_for_training(self, training: Subview):
        target_name = common.get_training_attribute(training, "target")
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

        self._say(
            "Found target[{0}] path: {0}".format(target_name, dst_path), log_only=True)

        return dst_path

    def _get_items_for_duration(self, items, requested_duration):
        """ fixme: this must become much more accurate - the entire selection concept is to be revisited
        """
        selected = []
        total_time = 0
        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items(items, "length")

        if _avg > 0:
            est_num_songs = round(requested_duration * 60 / _avg)
        else:
            est_num_songs = 0

        if est_num_songs > 0:
            bin_size = len(items) / est_num_songs
        else:
            bin_size = 0

        self._say("Estimated number of songs: {}".format(est_num_songs), log_only=True)
        self._say("Bin Size: {}".format(bin_size), log_only=True)

        for i in range(0, est_num_songs):
            bin_start = round(i * bin_size)
            bin_end = round(bin_start + bin_size)
            song_index = random.randint(bin_start, bin_end)
            try:
                item: Item = items[song_index]
            except IndexError:
                continue

            song_len = round(item.get("length"))
            total_time += song_len
            selected.append(item)

        self._say("Total time in list: {}".format(common.get_human_readable_time(total_time)), log_only=True)

        if total_time < requested_duration * 60:
            self._say("Song list is too short!!!", log_only=True)

        return selected

    def _get_training_query_element_keys(self, training):
        answer = []
        query_elements = self._gather_query_elements(training)
        for el in query_elements:
            answer.append(el.split(":")[0])

        return answer

    def _gather_query_elements(self, training: Subview):
        """Order(strongest to weakest): command -> training -> flavours
        """
        command_query = self.query
        training_query = []
        flavour_query = []

        # Append the query elements from the configuration
        tconf = common.get_training_attribute(training, "query")
        if tconf:
            for key in tconf.keys():
                training_query.append(common.get_beet_query_formatted_string(key, tconf.get(key)))

        # Append the query elements from the flavours defined on the training
        flavours = common.get_training_attribute(training, "use_flavours")
        if flavours:
            flavours = [flavours] if type(flavours) == str else flavours
            for flavour_name in flavours:
                flavour: Subview = self.config["flavours"][flavour_name]
                flavour_query += common.get_flavour_elements(flavour)

        self._say("Command query elements: {}".format(command_query), log_only=True)
        self._say("Training query elements: {}".format(training_query), log_only=True)
        self._say("Flavour query elements: {}".format(flavour_query), log_only=True)

        raw_combined_query = command_query + training_query + flavour_query
        self._say("Raw combined query elements: {}".format(raw_combined_query), log_only=True)

        # Remove duplicate keys
        combined_query = []
        used_keys = []
        for query_part in raw_combined_query:
            key = parse_query_part(query_part)[0]
            if key not in used_keys:
                used_keys.append(key)
                combined_query.append(query_part)

        self._say("Clean combined query elements: {}".format(combined_query), log_only=True)

        return combined_query

    def _retrieve_library_items(self, training: Subview):
        """Returns the results of the library query for a specific training
        The storing/overriding/restoring of the library.Item._types is made necessary
        by this issue: https://github.com/beetbox/beets/issues/3520
        Until the issue is solved this 'hack' is necessary.
        """
        full_query = self._gather_query_elements(training)

        # Store a copy of defined types and update them with our own overrides
        original_types = library.Item._types.copy()
        override_types = common.get_item_attribute_type_overrides()
        library.Item._types.update(override_types)

        # Execute the query parsing (this will use our own overrides)
        parsed_query = parse_query_string(" ".join(full_query), Item)[0]

        # Restore the original types
        library.Item._types = original_types.copy()

        self._say("Song selection query: {}".format(parsed_query), log_only=True)

        return self.lib.items(parsed_query)

    def display_library_items(self, items, fields, prefix=""):
        fmt = prefix
        for field in fields:
            if field in ["artist", "album", "title"]:
                fmt += "- {{{0}}} ".format(field)
            else:
                fmt += "[{0}: {{{0}}}] ".format(field)

        for item in items:
            kwargs = {}
            for field in fields:
                fld_val = None
                if hasattr(item, field):
                    fld_val = item[field]

                    if type(fld_val) in [float, int]:
                        fld_val = round(fld_val, 3)
                        fld_val = "{:7.3f}".format(fld_val)

                kwargs[field] = fld_val
            try:
                self._say(fmt.format(**kwargs))
            except IndexError:
                pass

    def list_trainings(self):
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
            self._say("Training[{0}] does not exist.".format(training_name), log_only=True)
            return

        display_name = "[   {}   ]".format(training_name)
        self._say("\n{0}".format(display_name.center(80, "=")))

        training: Subview = self.config["trainings"][training_name]
        training_keys = list(set(common.MUST_HAVE_TRAINING_KEYS) | set(training.keys()))
        final_keys = ["duration", "query", "use_flavours", "combined_query", "ordering", "target"]
        final_keys.extend(tk for tk in training_keys if tk not in final_keys)

        for key in final_keys:
            val = common.get_training_attribute(training, key)

            # Handle non-existent (made up) keys
            if key == "combined_query" and common.get_training_attribute(training, "use_flavours"):
                val = self._gather_query_elements(training)

            if val is None:
                continue

            if key == "duration":
                val = common.get_human_readable_time(val * 60)
            elif key == "ordering":
                val = dict(val)
            elif key == "query":
                pass

            if isinstance(val, dict):
                value = []
                for k in val:
                    value.append("{key}({val})".format(key=k, val=val[k]))
                val = ", ".join(value)

            self._say("{0}: {1}".format(key, val))

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

    def _say(self, msg, log_only=False):
        log_only = True if self.cfg_quiet else log_only
        common.say(msg, log_only)
