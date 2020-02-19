#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 12:40 PM
#  License: See LICENSE.txt
#

from logging import Logger
from random import randint

from beets.library import Item

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

    def test_item_randomizer(self):
        items = None
        duration = 5
        with self.assertRaises(TypeError):
            GRC.get_randomized_items(items, duration)

        items = []
        duration = 0
        self.assertEqual([], GRC.get_randomized_items(items, duration))

        items = []
        duration = 5
        self.assertEqual([], GRC.get_randomized_items(items, duration))

        items = []
        items_duration = 0
        for i in range(100):
            length = randint(60, 300)
            items_duration += length
            item = Item()
            item.update({"title": "Song-{}".format(length), "length": length})
            items.append(item)

        max_duration_min = 90
        rnd_items = GRC.get_randomized_items(items, max_duration_min)
        self.assertNotEqual(items, rnd_items)
        rnd_items_duration = GRC.get_duration_of_items(rnd_items)
        self.assertLess(rnd_items_duration, max_duration_min * 60)



