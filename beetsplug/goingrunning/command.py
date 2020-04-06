#  Copyright: Copyright (c) 2020., Adam Jakab
#  Author: Adam Jakab <adam at jakab dot pro>
#  License: See LICENSE.txt

from optparse import OptionParser

from beets import library
from beets.dbcore import query
from beets.dbcore.db import Results
from beets.dbcore.queryparse import parse_query_part, construct_query_part
from beets.library import Library, Item
from beets.ui import Subcommand, decargs
from beets.util.confit import Subview
from beetsplug.goingrunning import common
from beetsplug.goingrunning import itemexport
from beetsplug.goingrunning import itemorder
from beetsplug.goingrunning import itempick


class GoingRunningCommand(Subcommand):
    config: Subview = None
    lib: Library = None
    query = []
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
        if not common.get_destination_path_for_training(training):
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

        # 5) Clean, Copy, Playlist, Run
        itemexport.generate_output(training, sel_items, self.cfg_dry_run)
        self._say("Run!", log_only=False)

    def _get_training_query_element_keys(self, training):
        # todo: move to common
        answer = []
        query_elements = self._gather_query_elements(training)
        for el in query_elements:
            key = parse_query_part(el)[0]
            if key not in answer:
                answer.append(key)

        return answer

    def _gather_query_elements(self, training: Subview):
        """Sum all query elements into one big list ordered from strongest to
        weakest: command -> training -> flavours
        """
        command_query = self.query
        training_query = []
        flavour_query = []

        # Append the query elements from the configuration
        tconf = common.get_training_attribute(training, "query")
        if tconf:
            for key in tconf.keys():
                nqe = common.get_normalized_query_element(key, tconf.get(key))
                if type(nqe) == list:
                    training_query.extend(nqe)
                else:
                    training_query.append(nqe)

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

        raw_combined_query = command_query + training_query + flavour_query

        self._say("Combined query elements: {}".
                  format(raw_combined_query), log_only=True)

        return raw_combined_query

    def parse_query_elements(self, query_elements, model_cls):
        registry = {}

        # Iterate through elements and group them in a registry by field name
        for query_element in query_elements:
            key, term, query_class, negate = parse_query_part(query_element)
            if not key:
                continue
            # treat negated keys separately
            _reg_key = "^{}".format(key) if negate else key
            if _reg_key not in registry.keys():
                registry[_reg_key] = []
            registry[_reg_key].append({
                "key": key,
                "term": term,
                "query_class": query_class,
                "negate": negate,
                "q_string": query_element
            })

        def parse_and_merge_items(k, lst, cls):
            parsed_items = []
            is_negated = lst[0]["negate"]

            for item in lst:
                prefixes = {}
                qp = construct_query_part(cls, prefixes, item["q_string"])
                parsed_items.append(qp)

            if len(parsed_items) == 1:
                answer = parsed_items.pop()
            else:
                if is_negated:
                    answer = query.AndQuery(parsed_items)
                else:
                    answer = query.OrQuery(parsed_items)

            return answer

        query_parts = []
        for key in registry.keys():
            reg_item_list = registry[key]
            parsed_and_merged = parse_and_merge_items(
                key, reg_item_list, model_cls)
            self._say("{}: {}".format(key, parsed_and_merged))
            query_parts.append(parsed_and_merged)

        if len(query_parts) == 0:
            query_parts.append(query.TrueQuery())

        return query.AndQuery(query_parts)

    def _retrieve_library_items(self, training: Subview):
        """Returns the results of the library query for a specific training
        The storing/overriding/restoring of the library.Item._types
        is made necessary by this issue:
        https://github.com/beetbox/beets/issues/3520
        Until the issue is solved this 'hack' is necessary.
        """
        full_query = self._gather_query_elements(training)

        # Store a copy of defined types and update them with our own overrides
        original_types = library.Item._types.copy()
        override_types = common.get_item_attribute_type_overrides()
        library.Item._types.update(override_types)

        # Execute the query parsing (using our own type overrides)
        parsed_query = self.parse_query_elements(full_query, Item)

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
