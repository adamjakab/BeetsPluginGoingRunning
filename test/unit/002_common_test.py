#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 3/17/20, 3:28 PM
#  License: See LICENSE.txt
#

from logging import Logger

from beets.dbcore import types
from beetsplug.goingrunning import common, GoingRunningPlugin

from test.helper import UnitTestHelper, get_plugin_configuration, \
    capture_log


class CommonTest(UnitTestHelper):
    """Test methods in the beetsplug.goingrunning.common module
    """

    def test_module_values(self):
        self.assertTrue(hasattr(common, "MUST_HAVE_TRAINING_KEYS"))
        self.assertTrue(hasattr(common, "MUST_HAVE_TARGET_KEYS"))
        self.assertTrue(hasattr(common, "KNOWN_NUMERIC_FLEX_ATTRIBUTES"))
        self.assertTrue(hasattr(common, "KNOWN_TEXTUAL_FLEX_ATTRIBUTES"))
        self.assertTrue(hasattr(common, "__logger__"))
        self.assertIsInstance(common.__logger__, Logger)

    def test_say(self):
        test_message = "one two three"

        with capture_log() as logs:
            common.say(test_message)
        self.assertIn(test_message, '\n'.join(logs))

    def test_get_item_attribute_type_overrides(self):
        res = common.get_item_attribute_type_overrides()
        self.assertListEqual(common.KNOWN_NUMERIC_FLEX_ATTRIBUTES,
                             list(res.keys()))

        exp_types = [types.Float for n in
                     range(0, len(common.KNOWN_NUMERIC_FLEX_ATTRIBUTES))]
        res_types = [type(v) for v in res.values()]
        self.assertListEqual(exp_types, res_types)

    def test_get_beets_global_config(self):
        self.assertEqual("0:00:00", common.get_human_readable_time(0),
                         "Bad time format!")
        self.assertEqual("0:00:33", common.get_human_readable_time(33),
                         "Bad time format!")
        self.assertEqual("0:33:33", common.get_human_readable_time(2013),
                         "Bad time format!")
        self.assertEqual("3:33:33", common.get_human_readable_time(12813),
                         "Bad time format!")

    def test_get_flavour_elements(self):
        cfg = {
            "flavours": {
                "speedy": {
                    "bpm": "180..",
                    "genre": "Hard Rock",
                }
            }
        }
        config = get_plugin_configuration(cfg)
        self.assertListEqual(["bpm:180..", "genre:Hard Rock"],
                             common.get_flavour_elements(
                                 config["flavours"]["speedy"]))
        self.assertListEqual([], common.get_flavour_elements(
            config["flavours"]["not_there"]))

    def test_get_training_attribute(self):
        cfg = {
            "trainings": {
                "fallback": {
                    "query": {
                        "bpm": "120..",
                    },
                    "target": "MPD1",
                },
                "10K": {
                    "query": {
                        "bpm": "180..",
                        "length": "60..240",
                    },
                    "use_flavours": ["f1", "f2"],
                }
            }
        }
        config = get_plugin_configuration(cfg)
        training = config["trainings"]["10K"]

        # Direct
        self.assertEqual(cfg["trainings"]["10K"]["query"], common.get_training_attribute(training, "query"))
        self.assertEqual(cfg["trainings"]["10K"]["use_flavours"],
                         common.get_training_attribute(training, "use_flavours"))

        # Fallback
        self.assertEqual(cfg["trainings"]["fallback"]["target"], common.get_training_attribute(training, "target"))

        # Inexistent
        self.assertEqual(None, common.get_training_attribute(training, "hoppa"))

    def test_get_target_attribute(self):
        cfg = {
            "targets": {
                "MPD1": {
                    "device_root": "/media/mpd1/",
                    "device_path": "auto/",
                }
            }
        }
        config = get_plugin_configuration(cfg)
        target = config["targets"]["MPD1"]

        self.assertEqual("/media/mpd1/", common.get_target_attribute(target, "device_root"))
        self.assertEqual("auto/", common.get_target_attribute(target, "device_path"))
        self.assertEqual(None, common.get_target_attribute(target, "not_there"))

    def test_get_duration_of_items(self):
        items = [self.create_item(length=120), self.create_item(length=79)]
        self.assertEqual(199, common.get_duration_of_items(items))

        # ValueError
        baditem = self.create_item(length="")
        self.assertEqual(0, common.get_duration_of_items([baditem]))

        # TypeError
        baditem = self.create_item(length={})
        self.assertEqual(0, common.get_duration_of_items([baditem]))

    def test_get_min_max_sum_avg_for_items(self):
        item1 = self.create_item(mood_happy=100)
        item2 = self.create_item(mood_happy=150)
        item3 = self.create_item(mood_happy=200)
        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items([item1, item2, item3], "mood_happy")
        self.assertEqual(100, _min)
        self.assertEqual(200, _max)
        self.assertEqual(450, _sum)
        self.assertEqual(150, _avg)

        item1 = self.create_item(mood_happy=99.7512345)
        item2 = self.create_item(mood_happy=150.482234)
        item3 = self.create_item(mood_happy=200.254733)
        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items([item1, item2, item3], "mood_happy")
        self.assertEqual(99.751, _min)
        self.assertEqual(200.255, _max)
        self.assertEqual(450.488, _sum)
        self.assertEqual(150.163, _avg)

        # ValueError
        item1 = self.create_item(mood_happy=100)
        item2 = self.create_item(mood_happy="")
        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items([item1, item2], "mood_happy")
        self.assertEqual(100, _min)
        self.assertEqual(100, _max)
        self.assertEqual(100, _sum)
        self.assertEqual(100, _avg)

        # TypeError
        item1 = self.create_item(mood_happy=100)
        item2 = self.create_item(mood_happy={})
        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items(
            [item1, item2], "mood_happy")
        self.assertEqual(100, _min)
        self.assertEqual(100, _max)
        self.assertEqual(100, _sum)
        self.assertEqual(100, _avg)

    def test_get_class_instance(self):
        module_name = 'beetsplug.goingrunning'
        class_name = 'GoingRunningPlugin'
        instance = common.get_class_instance(module_name, class_name)
        self.assertIsInstance(instance, GoingRunningPlugin)

        with self.assertRaises(RuntimeError):
            module_name = 'beetsplug.goingtosleep'
            common.get_class_instance(module_name, class_name)

        with self.assertRaises(RuntimeError):
            module_name = 'beetsplug.goingrunning'
            class_name = 'GoingToSleepPlugin'
            common.get_class_instance(module_name, class_name)
