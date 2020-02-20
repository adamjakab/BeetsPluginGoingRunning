#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 5:44 PM
#  License: See LICENSE.txt
#
from random import randint

from beets.util.confit import Subview

from test.helper import TestHelper, Assertions, PLUGIN_NAME, capture_stdout


class BasicCommandTest(TestHelper, Assertions):

    def test_training_listing_long(self):
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "--list")

        self.assertIn("You have not created any trainings yet.", out.getvalue())

    def test_training_listing_short(self):
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "-l")

        self.assertIn("You have not created any trainings yet.", out.getvalue())

    def test_training_listing(self):
        self.reset_beets(config_file=b"config_user.yml")

        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "--list")

        output = out.getvalue()
        self.assertIn("::: training-1", output)
        self.assertIn("::: training-2", output)
        self.assertIn("::: marathon", output)

    def test_training_handling_inexistent(self):
        self.reset_beets(config_file=b"config_user.yml")

        training_name = "sitting_on_the_sofa"
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name)

        self.assertIn("There is no training[{0}] registered with this name!".format(training_name), out.getvalue())

    def test_training_training_song_count(self):
        self.reset_beets(config_file=b"config_user.yml")

        training_name = "marathon"
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name, "--count")

        count = 0
        self.assertIn("Number of songs: {}".format(count), out.getvalue())

    def test_training_no_songs(self):
        self.reset_beets(config_file=b"config_user.yml")

        training_name = "marathon"
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name)

        self.assertIn("Handling training: {0}".format(training_name), out.getvalue())
        self.assertIn("There are no songs in your library that match this training!", out.getvalue())

    def test_training_bad_target_1(self):
        self.reset_beets(config_file=b"config_user.yml")
        self.add_multiple_items_to_library(count=1, song_bpm=[145, 145], song_length=[120, 120])

        training_name = "bad-target-1"
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name)

        target_name = "inexistent_target"
        self.assertIn("The target name[{0}] is not defined!".format(target_name), out.getvalue())

    def test_training_bad_target_2(self):
        self.reset_beets(config_file=b"config_user.yml")
        self.add_multiple_items_to_library(count=1, song_bpm=[145, 145], song_length=[120, 120])

        training_name = "bad-target-2"
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name)

        target_name = "drive_not_connected"
        target_path = "/media/this/probably/does/not/exist"
        self.assertIn("The target[{0}] path does not exist: {1}".format(target_name, target_path), out.getvalue())

    def test_training_with_songs(self):
        self.reset_beets(config_file=b"config_user.yml")

        self.add_multiple_items_to_library(count=30, song_bpm=[150, 180], song_length=[120, 240])
        #self.runcli("ls")

        training_name = "one-hour-run"
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name)

        self.assertIn("Handling training: {0}".format(training_name), out.getvalue())
        self.assertIn("Number of songs selected:", out.getvalue())
        self.assertIn("Run!", out.getvalue())








