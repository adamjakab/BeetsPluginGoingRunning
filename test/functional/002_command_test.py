#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 3/17/20, 10:44 PM
#  License: See LICENSE.txt
#

from beets.util.confit import Subview

from test.helper import FunctionalTestHelper, Assertions, PLUGIN_NAME, PLUGIN_SHORT_DESCRIPTION, capture_log, \
    capture_stdout


class CommandTest(FunctionalTestHelper, Assertions):
    """Command related tests
    """

    def test_plugin_version(self):
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "--version")

        from beetsplug.goingrunning.version import __version__
        self.assertIn("Goingrunning(beets-{})".format(PLUGIN_NAME), out.getvalue())
        self.assertIn("v{}".format(__version__), out.getvalue())

    def test_training_listing_empty(self):
        self.reset_beets(config_file=b"empty.yml")
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "--list")
        self.assertIn("You have not created any trainings yet.", out.getvalue())

        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "-l")
        self.assertIn("You have not created any trainings yet.", out.getvalue())

    def test_training_listing_default(self):
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "--list")

        output = out.getvalue()
        self.assertIn("::: training-1", output)
        self.assertIn("::: training-2", output)
        self.assertIn("::: marathon", output)

    def test_training_handling_inexistent(self):
        training_name = "sitting_on_the_sofa"
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name)

        self.assertIn("There is no training[{0}] registered with this name!".format(training_name), out.getvalue())

    def test_training_song_count(self):
        training_name = "marathon"
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name, "--count")
        self.assertIn("Number of songs available: {}".format(0), out.getvalue())

        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name, "-c")
        self.assertIn("Number of songs available: {}".format(0), out.getvalue())

    def test_training_no_songs(self):
        training_name = "marathon"
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name)

        self.assertIn("Handling training: {0}".format(training_name), out.getvalue())
        self.assertIn("There are no songs in your library that match this training!", out.getvalue())

    def test_training_undefined_target(self):
        self.add_single_item_to_library()

        training_name = "bad-target-1"
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name)

        target_name = "inexistent_target"
        self.assertIn("The target name[{0}] is not defined!".format(target_name), out.getvalue())

    def test_training_bad_target(self):
        self.add_single_item_to_library()

        training_name = "bad-target-2"
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name)

        target_name = "MPD_3"
        target_path = "/media/this/probably/does/not/exist/"
        self.assertIn("The target[{0}] path does not exist: {1}".format(target_name, target_path), out.getvalue())

    def test_training_with_songs_multiple_config(self):
        self.add_multiple_items_to_library(count=10, bpm=[120, 180], length=[120, 240])
        training_name = "training-1"
        self.ensure_training_target_path(training_name)

        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, training_name)

        self.assertIn("Handling training: {0}".format(training_name), out.getvalue())
        self.assertIn("Number of songs selected:", out.getvalue())
        self.assertIn("Run!", out.getvalue())
