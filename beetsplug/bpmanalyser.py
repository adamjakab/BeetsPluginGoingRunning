#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/15/20, 10:01 PM
#  License: See LICENSE.txt


import os
import logging
from optparse import OptionParser

# import beets
from beets import config as beets_global_config
from beets.library import Library as BeatsLibrary
from beets.plugins import BeetsPlugin
from beets.ui import Subcommand, decargs
from subprocess import Popen, PIPE

# Module methods
log = logging.getLogger('beets.bpmanalyser')


# Classes ###
class BpmAnalyserPlugin(BeetsPlugin):
    def __init__(self):
        super(BpmAnalyserPlugin, self).__init__()
        self.config.add({})

    def commands(self):
        return [BpmAnayserCommand(self.config)]


class BpmAnayserCommand(Subcommand):
    config = None
    lib = None
    query = None
    parser = None

    analyser_script_path = None

    write_to_file = True
    quiet = False

    def __init__(self, cfg):
        self.config = cfg.flatten()
        self.analyser_script_path = os.path.dirname(os.path.realpath(__file__)) + "/aubio_song_tempo_anayser.py"

        self.parser = OptionParser(usage='%prog training_name [options] [ADDITIONAL_QUERY...]')

        self.parser.add_option(
            '-q', '--quiet',
            action='store_true', dest='quiet', default=False,
            help=u'keep quiet'
        )

        # Keep this at the end
        super(BpmAnayserCommand, self).__init__(
            parser=self.parser,
            name='bpmanalyser',
            help=u'analyse your songs for tempo and write it into the bpm tag'
        )

    def func(self, lib: BeatsLibrary, options, arguments):
        self.quiet = options.quiet
        self.lib = lib
        arguments = decargs(arguments)
        self.query = arguments

        self.analyse_songs()

    def analyse_songs(self):
        # Setup the query
        query = self.query
        query_element = "bpm:0"
        query.append(query_element)

        # Get the library items
        items = self.lib.items(self.query)

        for item in items:
            item_path = item.get("path").decode("utf-8")
            log.debug("Analysing[{0}]...".format(item_path))

            bpm = int(self.get_bpm_from_analyser_script(item_path))
            self._say("Song[{0}] bpm: {1}".format(item_path, bpm))

            if bpm != 0:
                item['bpm'] = bpm
                if self.write_to_file:
                    item.try_write()
                item.store()

    def get_bpm_from_analyser_script(self, item_path):
        # the aubio/ffmpeg can have a really ugly output on sterr so we execute it in a subprocess:
        # [mp3float @ 0x7fb4c89eaa00] Could not update timestamps for skipped samples.
        # [mp3float @ 0x7fb4c89eaa00] Could not update timestamps for discarded samples.

        # self._say("SCRIPT:: {}".format(self.analyser_script_path))
        proc = Popen([self.analyser_script_path, item_path], stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        bpm = int(stdout.decode("utf-8"))
        # self._say("O: {}".format(stdout.decode("utf-8")))
        # self._say("E: {}".format(stderr.decode("utf-8")))

        return bpm

    def _say(self, msg):
        if not self.quiet:
            log.info(msg)
        else:
            log.debug(msg)
