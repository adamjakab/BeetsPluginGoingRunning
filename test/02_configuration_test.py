#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/17/20, 10:53 PM
#  License: See LICENSE.txt
#
import json

from beets.util.confit import Subview

from test.helper import TestHelper, Assertions, PLUGIN_NAME, capture_stdout
from beetsplug.goingrunning.command import GoingRunningCommand

class ConfigurationTest(TestHelper, Assertions):

    # def setUp(self):
    #     super().reset_beets(config_file=b"config_1.yml")

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
        super().reset_beets(config_file=b"config_1.yml")

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
        self.assertEqual(["drive_1", "drive_2", "drive_3"], list(targets.keys()))
        self.assertEqual(["~/Music/", "/mnt/UsbDrive", "/media/Storage"], list(targets.values()))
        self.assertTrue(cfg["clean_target"].get())

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
        #super().reset_beets(config_file=b"config_1.yml")

        #GoingRunningCommand.list_training_attributes(GoingRunningCommand(self.config), "training-3")


        # self._dump_config(cfg)
        pass




