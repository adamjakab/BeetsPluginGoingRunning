#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/17/20, 10:53 PM
#  License: See LICENSE.txt
#

from unittest import TestCase

from beets.util.confit import Subview

from test.helper import TestHelper, capture_log, capture_stdout
from beets import config as beets_global_config
from beets import plugins
from beetsplug import goingrunning

_PLUGIN_NAME_ = 'goingrunning'
_PLUGIN_SHORT_DESCRIPTION_ = 'bring some music with you that matches your training'


class CompletionTest(TestHelper):
    """Test invocation of ``beet goingrunning`` with this plugin.
    Only ensures that command does not fail.
    """

    def test_application(self):
        with capture_stdout() as out:
            self.runcli()

        self.assertIn(_PLUGIN_NAME_, out.getvalue())
        self.assertIn(_PLUGIN_SHORT_DESCRIPTION_, out.getvalue())

    def test_application_plugin_list(self):
        with capture_stdout() as out:
            self.runcli("version")

        self.assertIn("plugins: {0}".format(_PLUGIN_NAME_), out.getvalue())

    def test_plugin(self):
        self.runcli(_PLUGIN_NAME_)


class ModuleTest(TestHelper):

    def test_must_have_training_keys(self):
        must_have_keys = ['song_bpm', 'song_len', 'duration', 'target']
        for key in must_have_keys:
            self.assertIn(key, goingrunning.MUST_HAVE_TRAINING_KEYS,
                          msg=u'Missing default training key: {0}'.format(key))

    def test_log_interface(self):
        self.assertTrue(goingrunning.log)

        msg = "Anything goes tonight!"
        with capture_log() as logs:
            goingrunning.log.info(msg)

        self.assertIn('{0}: {1}'.format(_PLUGIN_NAME_, msg), '\n'.join(logs))

    def test_get_beets_global_config(self):
        beets_cfg = beets_global_config
        plg_cfg = goingrunning.get_beets_global_config()
        self.assertEqual(beets_cfg, plg_cfg)

    def test_human_readable_time(self):
        self.assertEqual(goingrunning.get_human_readable_time(0), "0:00:00", "Bad Time!")
        self.assertEqual(goingrunning.get_human_readable_time(30), "0:00:30", "Bad Time!")
        self.assertEqual(goingrunning.get_human_readable_time(90), "0:01:30", "Bad Time!")
        self.assertEqual(goingrunning.get_human_readable_time(600), "0:10:00", "Bad Time!")


class ConfigurationTest(TestHelper):

    def test_has_plugin_default_config(self):
        self.assertIsInstance(self.config[_PLUGIN_NAME_], Subview)

    def test_plugin_default_config_keys(self):
        cfg: Subview = self.config[_PLUGIN_NAME_]
        cfg_keys = cfg.keys()
        def_keys = ['duration', 'targets', 'target', 'clean_target', 'song_bpm', 'song_len']
        self.assertEqual(cfg_keys.sort(), def_keys.sort())

        print(cfg)

    def test_training_listing_long(self):
        with capture_stdout() as out:
            self.runcli(_PLUGIN_NAME_, "--list")

        self.assertIn("You have not created any trainings yet.", out.getvalue())

    def test_training_listing_short(self):
        with capture_stdout() as out:
            self.runcli(_PLUGIN_NAME_, "-l")

        self.assertIn("You have not created any trainings yet.", out.getvalue())

    def test_training_listing_root_level_config(self):
        """
        These values come from the default configuration values at root level
        through method: _get_config_value_bubble_up
        :return:
        """
        cfg: Subview = self.config[_PLUGIN_NAME_]
        cfg.add({'trainings': {
            'marathon': {}
        }})

        with capture_stdout() as out:
            self.runcli(_PLUGIN_NAME_, "-l")

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
        cfg: Subview = self.config[_PLUGIN_NAME_]
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
            self.runcli(_PLUGIN_NAME_, "-l")

        output = out.getvalue()
        self.assertIn("::: marathon", output)
        self.assertIn("duration: {0}".format(marathon_cfg["duration"]), output)
        self.assertIn("song_bpm: {0}".format(marathon_cfg["song_bpm"]), output)
        self.assertIn("song_len: {0}".format(marathon_cfg["song_len"]), output)
        self.assertIn("target: {0}".format(marathon_cfg["target"]), output)









