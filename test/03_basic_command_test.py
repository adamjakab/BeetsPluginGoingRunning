#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 5:44 PM
#  License: See LICENSE.txt
#

from beets.util.confit import Subview

from test.helper import TestHelper, Assertions, PLUGIN_NAME, capture_stdout


class BasicCommandTest(TestHelper, Assertions):

    # def setUp(self):
    #     super().reset_beets(config_file=b"config_1.yml")

    def test_training_listing_long(self):
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "--list")

        self.assertIn("You have not created any trainings yet.", out.getvalue())

    def test_training_listing_short(self):
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "-l")

        self.assertIn("You have not created any trainings yet.", out.getvalue())

    def test_training_listing_root_level_config(self):
        """
        These values come from the default configuration values at root level
        through method: _get_config_value_bubble_up
        :return:
        """
        cfg: Subview = self.config[PLUGIN_NAME]
        cfg.add({'trainings': {
            'marathon': {}
        }})

        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "-l")

        output = out.getvalue()
        self.assertIn("::: marathon", output)
        self.assertIn("duration: {0}".format(cfg["duration"].get()), output)
        self.assertIn("song_bpm: {0}".format(cfg["song_bpm"].get()), output)
        self.assertIn("song_len: {0}".format(cfg["song_len"].get()), output)
        self.assertIn("target: {0}".format(cfg["target"].get()), output)

    def test_training_listing_training_level_config(self):
        """
        These values come from the default configuration values at root level
        through method: _get_config_value_bubble_up
        :return:
        """
        cfg: Subview = self.config[PLUGIN_NAME]
        marathon_cfg = {
            'song_bpm': [110, 130],
            'song_len': [120, 300],
            'duration': 119,
            'target': False
        }
        cfg.add({'trainings': {
            'marathon': marathon_cfg
        }})

        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "-l")

        output = out.getvalue()
        self.assertIn("::: marathon", output)
        self.assertIn("duration: {0}".format(marathon_cfg["duration"]), output)
        self.assertIn("song_bpm: {0}".format(marathon_cfg["song_bpm"]), output)
        self.assertIn("song_len: {0}".format(marathon_cfg["song_len"]), output)
        self.assertIn("target: {0}".format(marathon_cfg["target"]), output)

