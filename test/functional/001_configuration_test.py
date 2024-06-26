#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 12:35 PM
#  License: See LICENSE.txt
#

from confuse import Subview

from test.helper import FunctionalTestHelper, PLUGIN_NAME


class ConfigurationTest(FunctionalTestHelper):
    """Configuration related tests
    """

    def test_plugin_no_config(self):
        self.setup_beets({"config_file": b"empty.yml"})
        self.assertTrue(self.config.exists())
        self.assertTrue(self.config[PLUGIN_NAME].exists())
        self.assertIsInstance(self.config[PLUGIN_NAME], Subview)
        self.assertTrue(self.config[PLUGIN_NAME]["targets"].exists())
        self.assertTrue(self.config[PLUGIN_NAME]["trainings"].exists())
        self.assertTrue(self.config[PLUGIN_NAME]["flavours"].exists())

    def test_obsolete_config(self):
        self.setup_beets({"config_file": b"obsolete.yml"})
        logged = self.run_with_log_capture(PLUGIN_NAME)
        self.assertIn("INCOMPATIBLE PLUGIN CONFIGURATION", logged)
        self.assertIn("Offending key in training(training-1): song_bpm", logged)

    def test_default_config_sanity(self):
        self.setup_beets({"config_file": b"default.yml"})
        self.assertTrue(self.config[PLUGIN_NAME].exists())
        cfg = self.config[PLUGIN_NAME]

        # Check keys
        cfg_keys = cfg.keys()
        cfg_keys.sort()
        chk_keys = ['targets', 'trainings', 'flavours']
        chk_keys.sort()
        self.assertEqual(chk_keys, cfg_keys)

    def test_default_config_targets(self):
        self.setup_beets({"config_file": b"default.yml"})
        """ Check Targets"""
        cfg: Subview = self.config[PLUGIN_NAME]
        targets = cfg["targets"]
        self.assertTrue(targets.exists())

        self.assertIsInstance(targets, Subview)
        self.assertEqual(["MPD_1", "MPD_2", "MPD_3"], list(targets.get().keys()))

        # MPD 1
        target = targets["MPD_1"]
        self.assertIsInstance(target, Subview)
        self.assertTrue(target.exists())
        self.assertEqual("/tmp/", target["device_root"].get())
        self.assertEqual("Music/", target["device_path"].get())
        self.assertTrue(target["clean_target"].get())
        self.assertEqual(["xyz.txt"], target["delete_from_device"].get())

        # MPD 2
        target = targets["MPD_2"]
        self.assertIsInstance(target, Subview)
        self.assertTrue(target.exists())
        self.assertEqual("/mnt/UsbDrive/", target["device_root"].get())
        self.assertEqual("Auto/Music/", target["device_path"].get())
        self.assertFalse(target["clean_target"].get())

        # MPD 3
        target = targets["MPD_3"]
        self.assertIsInstance(target, Subview)
        self.assertTrue(target.exists())
        self.assertEqual("/media/this/probably/does/not/exist/", target["device_root"].get())
        self.assertEqual("Music/", target["device_path"].get())

    def test_default_config_trainings(self):
        self.setup_beets({"config_file": b"default.yml"})
        """ Check Targets"""
        cfg: Subview = self.config[PLUGIN_NAME]
        trainings = cfg["trainings"]
        self.assertTrue(trainings.exists())

    def test_default_config_flavours(self):
        self.setup_beets({"config_file": b"default.yml"})
        """ Check Targets"""
        cfg: Subview = self.config[PLUGIN_NAME]
        flavours = cfg["flavours"]
        self.assertTrue(flavours.exists())
