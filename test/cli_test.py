#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/17/20, 10:53 PM
#  License: See LICENSE.txt
#

from unittest import TestCase
from test.helper import TestHelper, capture_log, capture_stdout
from beets import config as beets_global_config
from beetsplug import goingrunning

_PLUGIN_NAME_ = 'goingrunning'


class CompletionTest(TestHelper):
    """Test invocation of ``beet goingrunning`` with this plugin.
    Only ensures that command does not fail.
    """

    def test_application(self):
        self.runcli('')

    def test_plugin(self):
        self.runcli(_PLUGIN_NAME_)


class ModuleTest(TestCase):

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
        s = goingrunning.get_human_readable_time(0)
        self.assertEqual(s, "0:00:00", "Bad Time!")




