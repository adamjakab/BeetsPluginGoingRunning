#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 12:40 PM
#  License: See LICENSE.txt
#

from logging import Logger
from random import randint

from test.helper import TestHelper, Assertions, PLUGIN_NAME, capture_log

from beets import config as beets_global_config
from beetsplug.goingrunning import common as GRC


class CommonModuleTest(TestHelper, Assertions):

    def test_must_have_training_keys(self):
        must_have_keys = ['song_bpm', 'song_len', 'duration', 'target']
        for key in must_have_keys:
            self.assertIn(key, GRC.MUST_HAVE_TRAINING_KEYS,
                          msg=u'Missing default training key: {0}'.format(key))

    def test_log_interface(self):
        log = GRC.get_beets_logger()
        self.assertIsInstance(log, Logger)

        msg = "Anything goes tonight!"
        with capture_log() as logs:
            log.info(msg)

        self.assertIn('{0}: {1}'.format(PLUGIN_NAME, msg), '\n'.join(logs))

    def test_get_beets_global_config(self):
        beets_cfg = beets_global_config
        plg_cfg = GRC.get_beets_global_config()
        self.assertEqual(beets_cfg, plg_cfg)

    def test_human_readable_time(self):
        self.assertEqual("0:00:00", GRC.get_human_readable_time(0), "Bad time format!")
        self.assertEqual("0:00:30", GRC.get_human_readable_time(30), "Bad time format!")
        self.assertEqual("0:01:30", GRC.get_human_readable_time(90), "Bad time format!")
        self.assertEqual("0:10:00", GRC.get_human_readable_time(600), "Bad time format!")

    def test_duration_of_items(self):
        items = None
        self.assertEqual(0, GRC.get_duration_of_items(items))

        items = {}
        self.assertEqual(0, GRC.get_duration_of_items(items))

        items = []
        self.assertEqual(0, GRC.get_duration_of_items(items))

        items = []
        total = 0
        for i in range(100):
            length = randint(1, 300)
            total += length
            items.append({"length": length})
        self.assertEqual(total, GRC.get_duration_of_items(items))

        items = [{"length": 1}, {"length": {}}, {"length": "abc"}, {"length": None}]
        self.assertEqual(1, GRC.get_duration_of_items(items))



