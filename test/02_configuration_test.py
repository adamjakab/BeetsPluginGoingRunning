#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/17/20, 10:53 PM
#  License: See LICENSE.txt
#
import json

from beets.util.confit import Subview

from test.helper import TestHelper, Assertions, PLUGIN_NAME, capture_stdout


class ConfigurationTest(TestHelper, Assertions):

    # def setUp(self):
    #     super().reset_beets(config_file=b"config_1.yml")

    def test_has_plugin_default_config(self):
        self.assertTrue(self.config.exists())
        plg_cfg = self.config[PLUGIN_NAME]
        self.assertTrue(plg_cfg.exists())
        self.assertIsInstance(plg_cfg, Subview)

    def test_plugin_default_config_keys(self):
        cfg: Subview = self.config[PLUGIN_NAME]
        cfg_keys = cfg.keys()
        cfg_keys.sort()
        def_keys = ['duration', 'targets', 'target', 'clean_target', 'song_bpm', 'song_len']
        def_keys.sort()
        self.assertEqual(def_keys, cfg_keys)

    def test_loading_user_configuration(self):
        super().reset_beets(config_file=b"config_1.yml")

        cfg: Subview = self.config[PLUGIN_NAME]

        cfg_keys = cfg.keys()
        cfg_keys.sort()
        chk_keys = ['duration', 'targets', 'target', 'clean_target', 'song_bpm', 'song_len', 'trainings']
        chk_keys.sort()
        self.assertEqual(chk_keys, cfg_keys)


        # self._dump_config(cfg)





