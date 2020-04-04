#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 3/17/20, 10:44 PM
#  License: See LICENSE.txt
#

from test.helper import FunctionalTestHelper, PLUGIN_NAME, \
    PACKAGE_TITLE, PACKAGE_NAME, PLUGIN_VERSION, \
    get_value_separated_from_output, convert_time_to_seconds


class CommandTest(FunctionalTestHelper):
    """Command related tests
    """

    def test_plugin_version(self):
        self.setup_beets({"config_file": b"default.yml"})
        versioninfo = "{pt}({pn}) plugin for Beets: v{ver}".format(
            pt=PACKAGE_TITLE,
            pn=PACKAGE_NAME,
            ver=PLUGIN_VERSION
        )

        logged = self.run_with_log_capture(PLUGIN_NAME, "--version")
        self.assertIn(versioninfo, logged)

        logged = self.run_with_log_capture(PLUGIN_NAME, "-v")
        self.assertIn(versioninfo, logged)

    def test_training_listing_empty(self):
        self.setup_beets({"config_file": b"empty.yml"})
        logged = self.run_with_log_capture(PLUGIN_NAME, "--list")
        self.assertIn("You have not created any trainings yet.", logged)

        logged = self.run_with_log_capture(PLUGIN_NAME, "-l")
        self.assertIn("You have not created any trainings yet.", logged)

    def test_training_listing_default(self):
        self.setup_beets({"config_file": b"default.yml"})
        logged = self.run_with_log_capture(PLUGIN_NAME, "--list")
        self.assertIn("[   training-1   ]", logged)
        self.assertIn("[   training-2   ]", logged)
        self.assertIn("[   training-3   ]", logged)

    def test_training_handling_inexistent(self):
        self.setup_beets({"config_file": b"default.yml"})
        training_name = "sitting_on_the_sofa"
        logged = self.run_with_log_capture(PLUGIN_NAME, training_name)
        self.assertIn(
            "There is no training with this name[{}]!".format(
                training_name), logged)

    def test_training_song_count(self):
        self.setup_beets({"config_file": b"default.yml"})
        training_name = "training-1"
        self.ensure_training_target_path(training_name)
        logged = self.run_with_log_capture(PLUGIN_NAME, training_name,
                                           "--count")
        self.assertIn("Number of songs available: {}".format(0), logged)

        logged = self.run_with_log_capture(PLUGIN_NAME, training_name, "-c")
        self.assertIn("Number of songs available: {}".format(0), logged)

    def test_training_no_songs(self):
        self.setup_beets({"config_file": b"default.yml"})
        training_name = "training-1"
        self.ensure_training_target_path(training_name)
        logged = self.run_with_log_capture(PLUGIN_NAME, training_name)
        self.assertIn("Handling training: {0}".format(training_name), logged)
        self.assertIn(
            "No songs in your library match this training!",
            logged)

    def test_training_target_not_set(self):
        self.setup_beets({"config_file": b"default.yml"})
        self.add_single_item_to_library()
        training_name = "bad-target-1"
        logged = self.run_with_log_capture(PLUGIN_NAME, training_name)
        self.assertIn(
            "Training does not declare a `target`!", logged)

    def test_training_undefined_target(self):
        self.setup_beets({"config_file": b"default.yml"})
        self.add_single_item_to_library()
        training_name = "bad-target-2"
        logged = self.run_with_log_capture(PLUGIN_NAME, training_name)
        target_name = "inexistent_target"
        self.assertIn(
            "The target name[{0}] is not defined!".format(target_name), logged)

    def test_training_bad_target(self):
        self.setup_beets({"config_file": b"default.yml"})
        self.add_single_item_to_library()
        training_name = "bad-target-3"
        logged = self.run_with_log_capture(PLUGIN_NAME, training_name)
        target_name = "MPD_3"
        target_path = "/media/this/probably/does/not/exist/"
        self.assertIn(
            "The target[{0}] path does not exist: {1}".format(target_name,
                                                              target_path),
            logged)

    def test_handling_training_1(self):
        """Simple query based song selection where everything matches
        """
        self.setup_beets({"config_file": b"default.yml"})
        training_name = "training-1"

        self.add_multiple_items_to_library(
            count=10,
            bpm=[120, 180],
            length=[120, 240]
        )

        self.ensure_training_target_path(training_name)

        logged = self.run_with_log_capture(PLUGIN_NAME, training_name)

        """ Output for "training-1":
        
        Handling training: training-1
        Available songs: 10
        Selected songs: 2
        Planned training duration: 0:10:00
        Total song duration: 0:05:55
        Selected: [bpm:137][year:0][length:175.0][artist:the ärtist][
        title:tïtle 7]
        Selected: [bpm:139][year:0][length:180.0][artist:the ärtist][
        title:tïtle 6]
        Cleaning target[MPD_1]: 
        /private/var/folders/yv/9ntm56m10ql9wf_1zkbw74hr0000gp/T/tmpa2soyuro
        /Music
        Deleting additional files: ['xyz.txt']
        Copying to target[MPD_1]: 
        /private/var/folders/yv/9ntm56m10ql9wf_1zkbw74hr0000gp/T/tmpa2soyuro
        /Music
        Run!
        """

        prefix = "Handling training:"
        self.assertIn(prefix, logged)
        value = get_value_separated_from_output(logged, prefix)
        self.assertEqual(training_name, value)

        prefix = "Available songs:"
        self.assertIn(prefix, logged)
        value = int(get_value_separated_from_output(logged, prefix))
        self.assertEqual(10, value)

        prefix = "Selected songs:"
        self.assertIn(prefix, logged)
        value = int(get_value_separated_from_output(logged, prefix))
        self.assertGreater(value, 0)
        self.assertLessEqual(value, 10)

        prefix = "Planned training duration:"
        self.assertIn(prefix, logged)
        value = get_value_separated_from_output(logged, prefix)
        seconds = convert_time_to_seconds(value)
        self.assertEqual("0:10:00", value)
        self.assertEqual(600, seconds)

        # Do not test for efficiency here
        prefix = "Total song duration:"
        self.assertIn(prefix, logged)
        value = get_value_separated_from_output(logged, prefix)
        seconds = convert_time_to_seconds(value)
        self.assertGreater(seconds, 0)

    def test_handling_training_2(self):
        """Simple flavour based song selection with float value matching
        """
        self.setup_beets({"config_file": b"default.yml"})
        training_name = "training-2"

        # Add matching items
        self.add_multiple_items_to_library(count=10,
                                           bpm=[170, 200],
                                           mood_aggressive=[0.7, 1],
                                           year=[1960, 1969],
                                           length=[120, 240]
                                           )
        # Add not matching items
        self.add_multiple_items_to_library(count=10,
                                           bpm=[120, 150],
                                           mood_aggressive=[0.2, 0.4],
                                           year=[1930, 1950],
                                           length=[120, 240]
                                           )

        self.ensure_training_target_path(training_name)

        logged = self.run_with_log_capture(PLUGIN_NAME, training_name)

        """ Output for "training-2":

        Handling training: training-2
        Available songs: 10
        Selected songs: 3
        Planned training duration: 0:10:00
        Total song duration: 0:09:03
        Selected: [bpm:175][year:1967][length:174.0][artist:the ärtist][
        title:tïtle 6]
        Selected: [bpm:181][year:1962][length:206.0][artist:the ärtist][
        title:tïtle 4]
        Selected: [bpm:197][year:1968][length:163.0][artist:the ärtist][
        title:tïtle 1]
        Cleaning target[MPD_1]: 
        /private/var/folders/yv/9ntm56m10ql9wf_1zkbw74hr0000gp/T/tmpgoh3gyo5
        /Music
        Deleting additional files: ['xyz.txt']
        Copying to target[MPD_1]: 
        /private/var/folders/yv/9ntm56m10ql9wf_1zkbw74hr0000gp/T/tmpgoh3gyo5
        /Music
        Run!

        """

        prefix = "Handling training:"
        self.assertIn(prefix, logged)
        value = get_value_separated_from_output(logged, prefix)
        self.assertEqual(training_name, value)

        prefix = "Available songs:"
        self.assertIn(prefix, logged)
        value = int(get_value_separated_from_output(logged, prefix))
        self.assertEqual(10, value)

        prefix = "Selected songs:"
        self.assertIn(prefix, logged)
        value = int(get_value_separated_from_output(logged, prefix))
        self.assertGreater(value, 0)
        self.assertLessEqual(value, 10)

        prefix = "Planned training duration:"
        self.assertIn(prefix, logged)
        value = get_value_separated_from_output(logged, prefix)
        seconds = convert_time_to_seconds(value)
        self.assertEqual("0:10:00", value)
        self.assertEqual(600, seconds)

        # Do not test for efficiency here
        prefix = "Total song duration:"
        self.assertIn(prefix, logged)
        value = get_value_separated_from_output(logged, prefix)
        seconds = convert_time_to_seconds(value)
        self.assertGreater(seconds, 0)

    def test_handling_training_3(self):
        """Simple query + flavour based song selection
        """
        self.setup_beets({"config_file": b"default.yml"})
        training_name = "training-3"

        # Add matching items for query + flavour
        self.add_multiple_items_to_library(count=10,
                                           bpm=[145, 160],
                                           genre="Reggae",
                                           length=[120, 240]
                                           )
        # Add partially matching items
        self.add_multiple_items_to_library(count=10,
                                           bpm=[145, 160],
                                           genre="Rock",
                                           length=[120, 240]
                                           )

        self.add_multiple_items_to_library(count=10,
                                           bpm=[100, 140],
                                           genre="Reggae",
                                           length=[120, 240]
                                           )

        self.ensure_training_target_path(training_name)

        logged = self.run_with_log_capture(PLUGIN_NAME, training_name)

        """ Output for "training-2":

        Handling training: training-3
        Available songs: 10
        Selected songs: 3
        Planned training duration: 0:10:00
        Total song duration: 0:07:26
        Selected: [bpm:158][year:0][length:141.0][artist:the ärtist][
        title:tïtle 3]
        Selected: [bpm:154][year:0][length:158.0][artist:the ärtist][
        title:tïtle 5]
        Selected: [bpm:152][year:0][length:147.0][artist:the ärtist][
        title:tïtle 10]
        Cleaning target[MPD_1]: 
        /private/var/folders/yv/9ntm56m10ql9wf_1zkbw74hr0000gp/T/tmpgnxlpeih
        /Music
        Deleting additional files: ['xyz.txt']
        Copying to target[MPD_1]: 
        /private/var/folders/yv/9ntm56m10ql9wf_1zkbw74hr0000gp/T/tmpgnxlpeih
        /Music
        Run!

        """

        prefix = "Handling training:"
        self.assertIn(prefix, logged)
        value = get_value_separated_from_output(logged, prefix)
        self.assertEqual(training_name, value)

        prefix = "Available songs:"
        self.assertIn(prefix, logged)
        value = int(get_value_separated_from_output(logged, prefix))
        self.assertEqual(10, value)

        prefix = "Selected songs:"
        self.assertIn(prefix, logged)
        value = int(get_value_separated_from_output(logged, prefix))
        self.assertGreater(value, 0)
        self.assertLessEqual(value, 10)

        prefix = "Planned training duration:"
        self.assertIn(prefix, logged)
        value = get_value_separated_from_output(logged, prefix)
        seconds = convert_time_to_seconds(value)
        self.assertEqual("0:10:00", value)
        self.assertEqual(600, seconds)

        # Do not test for efficiency here
        prefix = "Total song duration:"
        self.assertIn(prefix, logged)
        value = get_value_separated_from_output(logged, prefix)
        seconds = convert_time_to_seconds(value)
        self.assertGreater(seconds, 0)
