#  Copyright: Copyright (c) 2020., Adam Jakab
#  Author: Adam Jakab <adam at jakab dot pro>
#  License: See LICENSE.txt

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
from beets.library import Library, Item, parse_query_parts
from beets.ui import Subcommand, decargs
from beets.util.confit import Subview, NotFoundError
from beetsplug.goingrunning import common
from beetsplug.goingrunning import itemorder
from beetsplug.goingrunning import itempick


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

        self.parser = OptionParser(
            usage='beet {plg} [training] [options] [QUERY...]'.format(
                plg=common.plg_ns['__PLUGIN_NAME__']
            )
        )

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
            name=common.plg_ns['__PLUGIN_NAME__'],
            aliases=[common.plg_ns['__PLUGIN_ALIAS__']] \
                if common.plg_ns['__PLUGIN_ALIAS__'] else [],
            help=common.plg_ns['__PLUGIN_SHORT_DESCRIPTION__']
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
            self._say(
                "********************   INCOMPATIBLE PLUGIN CONFIGURATION   "
                "*********************")
            self._say("*" * 80)
            self._say(
                "* Your configuration has been created for an older version "
                "of the plugin.")
            self._say(
                "* Since version 1.1.1 the plugin has implemented changes "
                "that require your "
                "current configuration to be updated.")
            self._say(
                "* Please read the updated documentation here and update your "
                "configuration.")
            self._say(
                "* Documentation: "
                "https://github.com/adamjakab/BeetsPluginGoingRunning/blob"
                "/master/README.md"
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

        self._say("Handling training: {0}".format(training_name),
                  log_only=False)

        # todo: create a sanity checker for training to check all attributes
        if not training.exists():
            self._say(
                "There is no training with this name[{0}]!".format(
                    training_name), log_only=False)
            return

        # Verify target device path path
        if not self._get_destination_path_for_training(training):
            self._say(
                "Invalid target!", log_only=False)
            return

        # Get the library items
        lib_items: Results = self._retrieve_library_items(training)

        # Show count only
        if self.cfg_count:
            self._say("Number of songs available: {}".format(len(lib_items)),
                      log_only=False)
            return



        # Check count
        if len(lib_items) < 1:
            self._say(
                "No songs in your library match this training!", log_only=False)
            return

        duration = common.get_training_attribute(training, "duration")
        if not duration:
            self._say("There is no duration set for the selected training!",
                      log_only=False)
            return

        # 1) order items by `ordering_strategy`
        sorted_items = itemorder.get_ordered_items(training, lib_items)
        # flds = ["ordering_score", "artist", "title"]
        # self.display_library_items(sorted_items, flds, prefix="SORTED: ")

        # 2) select items that cover the training duration
        itempick.favour_unplayed = \
            common.get_training_attribute(training, "favour_unplayed")
        sel_items = itempick.get_items_for_duration(training, sorted_items,
                                                    duration * 60)

        # 3) Show some info
        total_time = common.get_duration_of_items(sel_items)
        self._say("Available songs: {}".format(len(lib_items)))
        self._say("Selected songs: {}".format(len(sel_items)))
        self._say("Planned training duration: {0}".format(
            common.get_human_readable_time(duration * 60)))
        self._say("Total song duration: {}".format(
            common.get_human_readable_time(total_time)))

        # 4) Show the selected songs
        flds = self._get_training_query_element_keys(training)
        flds += ["play_count", "artist", "title"]
        self.display_library_items(sel_items, flds, prefix="Selected: ")

        # 5) Clea, Copy, Run
        self._clean_target_path(training)
        self._copy_items_to_target(training, sel_items)
        self._say("Run!", log_only=False)

    def _clean_target_path(self, training: Subview):
        target_name = common.get_training_attribute(training, "target")

        if self._get_target_attribute_for_training(training, "clean_target"):
            dst_path = self._get_destination_path_for_training(training)

            self._say("Cleaning target[{0}]: {1}".
                      format(target_name, dst_path), log_only=False)
            song_extensions = ["mp3", "mp4", "flac", "wav", "ogg", "wma", "m3u"]
            target_file_list = []
            for ext in song_extensions:
                target_file_list += glob(
                    os.path.join(dst_path, "*.{}".format(ext)))

            for f in target_file_list:
                self._say("Deleting: {}".format(f))
                if not self.cfg_dry_run:
                    os.remove(f)

        additional_files = self._get_target_attribute_for_training(training,
                                                                   "delete_from_device")
        if additional_files and len(additional_files) > 0:
            root = self._get_target_attribute_for_training(training,
                                                           "device_root")
            root = Path(root).expanduser()

            self._say("Deleting additional files: {0}".
                      format(additional_files), log_only=False)

            for path in additional_files:
                path = Path(str.strip(path, "/"))
                dst_path = os.path.realpath(root.joinpath(path))

                if not os.path.isfile(dst_path):
                    self._say(
                        "The file to delete does not exist: {0}".format(path),
                        log_only=True)
                    continue

                self._say("Deleting: {}".format(dst_path))
                if not self.cfg_dry_run:
                    os.remove(dst_path)

    def _copy_items_to_target(self, training: Subview, rnd_items):
        target_name = common.get_training_attribute(training, "target")
        increment_play_count = common.get_training_attribute(
            training, "increment_play_count")
        dst_path = self._get_destination_path_for_training(training)
        self._say("Copying to target[{0}]: {1}".
                  format(target_name, dst_path), log_only=False)

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
            self._say("Copying[{1}]: {0}".format(src, gen_filename),
                      log_only=True)

            if not self.cfg_dry_run:
                copyfile(src, dst)
                if increment_play_count:
                    common.increment_play_count_on_item(item)

            cnt += 1

    def _get_target_for_training(self, training: Subview):
        target_name = common.get_training_attribute(training, "target")
        self._say("Finding target: {0}".format(target_name))

        if not self.config["targets"][target_name].exists():
            self._say(
                "The target name[{0}] is not defined!".format(target_name))
            return

        return self.config["targets"][target_name]

    def _get_target_attribute_for_training(self, training: Subview,
                                           attrib: str = "name"):
        target_name = common.get_training_attribute(training, "target")
        self._say("Getting attribute[{0}] for target: {1}".format(attrib,
                                                                  target_name),
                  log_only=True)
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
            "Found target[{0}] attribute[{1}] path: {2}".format(target_name,
                                                                attrib,
                                                                attrib_val),
            log_only=True)

        return attrib_val

    def _get_destination_path_for_training(self, training: Subview):
        target_name = common.get_training_attribute(training, "target")

        if not target_name:
            self._say(
                "Training does not declare a `target`!".
                    format(target_name), log_only=False)
            return

        root = self._get_target_attribute_for_training(training, "device_root")
        path = self._get_target_attribute_for_training(training, "device_path")
        path = path or ""

        if not root:
            self._say(
                "The target[{0}] does not declare a device root path.".
                    format(target_name), log_only=False)
            return

        root = Path(root).expanduser()
        path = Path(str.strip(path, "/"))
        dst_path = os.path.realpath(root.joinpath(path))

        if not os.path.isdir(dst_path):
            self._say(
                "The target[{0}] path does not exist: {1}".
                    format(target_name, dst_path), log_only=False)
            return

        self._say(
            "Found target[{0}] path: {0}".format(target_name, dst_path),
            log_only=True)

        return dst_path

    def _get_training_query_element_keys(self, training):
        answer = []
        query_elements = self._gather_query_elements(training)
        for el in query_elements:
            answer.append(el.split(":")[0])

        return answer

    def _gather_query_elements(self, training: Subview):
        """Sum all query elements and order them (strongest to weakest):
        command -> training -> flavours
        """
        command_query = self.query
        training_query = []
        flavour_query = []

        # Append the query elements from the configuration
        tconf = common.get_training_attribute(training, "query")
        if tconf:
            for key in tconf.keys():
                training_query.append(
                    common.get_query_element_string(key, tconf.get(key)))

        # Append the query elements from the flavours defined on the training
        flavours = common.get_training_attribute(training, "use_flavours")
        if flavours:
            flavours = [flavours] if type(flavours) == str else flavours
            for flavour_name in flavours:
                flavour: Subview = self.config["flavours"][flavour_name]
                flavour_query += common.get_flavour_elements(flavour)

        self._say("Command query elements: {}".format(command_query),
                  log_only=True)
        self._say("Training query elements: {}".format(training_query),
                  log_only=True)
        self._say("Flavour query elements: {}".format(flavour_query),
                  log_only=True)

        # Remove duplicate keys (first one wins)
        raw_combined_query = command_query + training_query + flavour_query
        combined_query = []
        used_keys = []
        for query_part in raw_combined_query:
            key = parse_query_part(query_part)[0]
            if key not in used_keys:
                used_keys.append(key)
                combined_query.append(query_part)

        self._say("Combined query elements: {}".format(combined_query),
                  log_only=True)

        return combined_query

    def _retrieve_library_items(self, training: Subview):
        """Returns the results of the library query for a specific training
        The storing/overriding/restoring of the library.Item._types is made
        necessary
        by this issue: https://github.com/beetbox/beets/issues/3520
        Until the issue is solved this 'hack' is necessary.
        """
        full_query = self._gather_query_elements(training)

        # Store a copy of defined types and update them with our own overrides
        original_types = library.Item._types.copy()
        override_types = common.get_item_attribute_type_overrides()
        library.Item._types.update(override_types)

        # Execute the query parsing (using our own type overrides)
        parsed_query, parsed_ordering = parse_query_parts(full_query, Item)

        # Restore the original types
        library.Item._types = original_types.copy()

        self._say("Parsed query: {}".format(parsed_query))

        return self.lib.items(parsed_query)

    def display_library_items(self, items, fields, prefix=""):
        fmt = prefix
        for field in fields:
            if field in ["artist", "album", "title"]:
                fmt += "- {{{0}}} ".format(field)
            else:
                fmt += "[{0}: {{{0}}}] ".format(field)

        common.say("{}".format("=" * 120), log_only=False)
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
                self._say(fmt.format(**kwargs), log_only=False)
            except IndexError:
                pass
        common.say("{}".format("=" * 120), log_only=False)

    def list_trainings(self):
        trainings = list(self.config["trainings"].keys())
        training_names = [s for s in trainings if s != "fallback"]

        if len(training_names) == 0:
            self._say("You have not created any trainings yet.")
            return

        self._say("Available trainings:", log_only=False)
        for training_name in training_names:
            self.list_training_attributes(training_name)

    def list_training_attributes(self, training_name: str):
        if not self.config["trainings"].exists() or not \
                self.config["trainings"][training_name].exists():
            self._say("Training[{0}] does not exist.".format(training_name),
                      is_error=True)
            return

        display_name = "[   {}   ]".format(training_name)
        self._say("\n{0}".format(display_name.center(80, "=")), log_only=False)

        training: Subview = self.config["trainings"][training_name]
        training_keys = list(
            set(common.MUST_HAVE_TRAINING_KEYS) | set(training.keys()))
        final_keys = ["duration", "query", "use_flavours", "combined_query",
                      "ordering", "target"]
        final_keys.extend(tk for tk in training_keys if tk not in final_keys)

        for key in final_keys:
            val = common.get_training_attribute(training, key)

            # Handle non-existent (made up) keys
            if key == "combined_query" and common.get_training_attribute(
                    training, "use_flavours"):
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

            self._say("{0}: {1}".format(key, val), log_only=False)

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
                    raise RuntimeError(
                        "Offending key in training({}): {}".format(
                            training_name, tkey))

    def show_version_information(self):
        self._say("{pt}({pn}) plugin for Beets: v{ver}".format(
            pt=common.plg_ns['__PACKAGE_TITLE__'],
            pn=common.plg_ns['__PACKAGE_NAME__'],
            ver=common.plg_ns['__version__']
        ), log_only=False)

    @staticmethod
    def _say(msg, log_only=True, is_error=False):
        common.say(msg, log_only, is_error)
