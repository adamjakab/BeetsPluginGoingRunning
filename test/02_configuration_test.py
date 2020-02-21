#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/17/20, 10:53 PM
#  License: See LICENSE.txt
#
import os

from beets.util.confit import Subview

from test.helper import TestHelper, Assertions, PLUGIN_NAME, capture_stdout, capture_log
from beetsplug.goingrunning.command import GoingRunningCommand
from beetsplug.goingrunning import common as GoingRunningCommon


class ConfigurationTest(TestHelper, Assertions):

    def test_has_plugin_default_config(self):
        self.assertTrue(self.config.exists())
        plg_cfg = self.config[PLUGIN_NAME]
        self.assertTrue(plg_cfg.exists())
        self.assertIsInstance(plg_cfg, Subview)

    def test_plugin_default_config_keys(self):
        """ Generic check to see if plugin related default configuration is present in config """
        cfg: Subview = self.config[PLUGIN_NAME]
        cfg_keys = cfg.keys()
        cfg_keys.sort()
        def_keys = ['duration', 'targets', 'target', 'clean_target', 'song_bpm', 'song_len']
        def_keys.sort()
        self.assertEqual(def_keys, cfg_keys)

    def test_loading_user_configuration(self):
        """ Generic check to see if plugin related configuration is present coming from user configuration file """
        self.reset_beets(config_file=b"config_user.yml")

        cfg: Subview = self.config[PLUGIN_NAME]

        # Check keys
        cfg_keys = cfg.keys()
        cfg_keys.sort()
        chk_keys = ['duration', 'targets', 'target', 'clean_target', 'song_bpm', 'song_len', 'trainings']
        chk_keys.sort()
        self.assertEqual(chk_keys, cfg_keys)

        # Check values
        self.assertEqual([0, 999], cfg["song_bpm"].get())
        self.assertEqual([0, 999], cfg["song_len"].get())
        self.assertEqual(120, cfg["duration"].get())
        self.assertEqual("drive_1", cfg["target"].get())
        targets = cfg["targets"].get()
        self.assertEqual(["drive_1", "drive_2", "drive_3", "drive_not_connected"], list(targets.keys()))
        self.assertEqual(["/tmp/beets-goingrunning-test-drive",
                          "/mnt/UsbDrive",
                          "~/Music/",
                          "/media/this/probably/does/not/exist"],
                         list(targets.values()))
        self.assertFalse(cfg["clean_target"].get())

        # Check values at Trainings level
        trainings = cfg["trainings"]
        self.assertTrue(trainings.exists())
        self.assertEqual([50, 200], trainings["song_bpm"].get())
        self.assertEqual([30, 600], trainings["song_len"].get())
        self.assertEqual(60, trainings["duration"].get())
        self.assertEqual("drive_2", trainings["target"].get())

        # Check Training-1
        t1 = trainings["training-1"]
        self.assertTrue(t1.exists())
        self.assertEqual([150, 180], t1["song_bpm"].get())
        self.assertEqual([120, 240], t1["song_len"].get())
        self.assertEqual(55, t1["duration"].get())
        self.assertEqual("drive_3", t1["target"].get())
        self.assertEqual("Born to run", t1["alias"].get())

        # Check Training-2
        t2 = trainings["training-2"]
        self.assertTrue(t2.exists())
        self.assertEqual([170, 180], t2["song_bpm"].get())
        self.assertEqual([90, 180], t2["song_len"].get())
        self.assertEqual(25, t2["duration"].get())
        self.assertEqual("drive_3", t2["target"].get())
        self.assertEqual("Born to run", t2["alias"].get())

    def test_method_list_training_attributes(self):
        """ Generic check to see if plugin related configuration is present coming from user configuration file """
        self.reset_beets(config_file=b"config_user.yml")
        plg = GoingRunningCommand(self.config[PLUGIN_NAME])

        name = "training-1"
        with capture_stdout() as out:
            plg.list_training_attributes(name)
        self.assertIn(name, out.getvalue())
        self.assertIn("alias: Born to run", out.getvalue())
        self.assertIn("duration: 55", out.getvalue())
        self.assertIn("song_bpm: [150, 180]", out.getvalue())
        self.assertIn("song_len: [120, 240]", out.getvalue())
        self.assertIn("target: drive_3", out.getvalue())

        name = "training-2"
        with capture_stdout() as out:
            plg.list_training_attributes(name)
        self.assertIn(name, out.getvalue())
        self.assertIn("alias: Born to run", out.getvalue())
        self.assertIn("duration: 25", out.getvalue())
        self.assertIn("song_bpm: [170, 180]", out.getvalue())
        self.assertIn("song_len: [90, 180]", out.getvalue())
        self.assertIn("target: drive_3", out.getvalue())

    def test_bubble_up(self):
        """ Check values when each level has its own  """
        self.reset_beets(config_file=b"config_user.yml")

        cfg_l1: Subview = self.config[PLUGIN_NAME]
        cfg_l2: Subview = cfg_l1["trainings"]
        cfg_l3: Subview = cfg_l2["training-1"]
        self._dump_config(self.config)

        # Each level has its own value
        for attrib in ['duration', 'target', 'song_bpm', 'song_len']:
            self.assertEqual(cfg_l3[attrib].get(), GoingRunningCommon.get_config_value_bubble_up(cfg_l3, attrib))
            self.assertEqual(cfg_l2[attrib].get(), GoingRunningCommon.get_config_value_bubble_up(cfg_l2, attrib))
            self.assertEqual(cfg_l1[attrib].get(), GoingRunningCommon.get_config_value_bubble_up(cfg_l1, attrib))

    def test_bubble_up_inexistent_key(self):
        """ Check values when each level has its own  """
        self.reset_beets(config_file=b"config_user.yml")
        cfg: Subview = self.config[PLUGIN_NAME]["trainings"]["training-1"]
        inexistent_key = "you_will_never_find_me"
        self.assertEqual(None, GoingRunningCommon.get_config_value_bubble_up(cfg, inexistent_key))

    def test_bubble_up_no_level_3(self):
        """ Check that values are taken from level 2 if they are not present on level 3 """
        self.reset_beets(config_file=b"config_user_no_level_3.yml")

        cfg_l1: Subview = self.config[PLUGIN_NAME]
        cfg_l2: Subview = cfg_l1["trainings"]
        cfg_l3: Subview = cfg_l2["training-1"]

        for attrib in ['duration', 'target', 'song_bpm', 'song_len']:
            self.assertEqual(cfg_l2[attrib].get(), GoingRunningCommon.get_config_value_bubble_up(cfg_l3, attrib))

    def test_bubble_up_no_level_3_or_2(self):
        """ Check that values are taken from level 1 if they are not present on level 3 or 2 """
        self.reset_beets(config_file=b"config_user_no_level_3_or_2.yml")

        cfg_l1: Subview = self.config[PLUGIN_NAME]
        cfg_l2: Subview = cfg_l1["trainings"]
        cfg_l3: Subview = cfg_l2["training-1"]

        for attrib in ['duration', 'target', 'song_bpm', 'song_len']:
            self.assertEqual(cfg_l1[attrib].get(), GoingRunningCommon.get_config_value_bubble_up(cfg_l3, attrib))

        self._dump_config(self.config)
