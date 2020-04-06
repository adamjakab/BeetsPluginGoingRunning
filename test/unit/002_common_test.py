#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 3/17/20, 3:28 PM
#  License: See LICENSE.txt
#
import os
from logging import Logger

from beets import util
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

    def test_get_human_readable_time(self):
        self.assertEqual("0:00:00", common.get_human_readable_time(0),
                         "Bad time format!")
        self.assertEqual("0:00:33", common.get_human_readable_time(33),
                         "Bad time format!")
        self.assertEqual("0:33:33", common.get_human_readable_time(2013),
                         "Bad time format!")
        self.assertEqual("3:33:33", common.get_human_readable_time(12813),
                         "Bad time format!")

    def test_get_normalized_query_element(self):
        # Test simple value pair(string)
        key = "genre"
        val = "Rock"
        expected = "genre:Rock"
        qe = common.get_normalized_query_element(key, val)
        self.assertEqual(expected, qe)

        # Test simple value pair(int)
        key = "length"
        val = 360
        expected = "length:360"
        qe = common.get_normalized_query_element(key, val)
        self.assertEqual(expected, qe)

        # Test list of values: ['bpm:100..120', 'bpm:160..180']
        key = "bpm"
        val = ["100..120", "160..180"]
        expected = ["bpm:100..120", "bpm:160..180"]
        qe = common.get_normalized_query_element(key, val)
        self.assertListEqual(expected, qe)

    def test_get_flavour_elements(self):
        cfg = {
            "flavours": {
                "speedy": {
                    "bpm": "180..",
                    "genre": "Hard Rock",
                },
                "complex": {
                    "bpm": "180..",
                    "genre": ["Rock", "Jazz", "Pop"],
                }
            }
        }
        config = get_plugin_configuration(cfg)

        # non-existent flavour
        el = common.get_flavour_elements(config["flavours"]["not_there"])
        self.assertListEqual([], el)

        # simple single values
        expected = ["bpm:180..", "genre:Hard Rock"]
        el = common.get_flavour_elements(config["flavours"]["speedy"])
        self.assertListEqual(expected, el)

        # list in field
        expected = ["bpm:180..", "genre:Rock", "genre:Jazz", "genre:Pop"]
        el = common.get_flavour_elements(config["flavours"]["complex"])
        self.assertListEqual(expected, el)

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
        self.assertEqual(cfg["trainings"]["10K"]["query"],
                         common.get_training_attribute(training, "query"))
        self.assertEqual(cfg["trainings"]["10K"]["use_flavours"],
                         common.get_training_attribute(training,
                                                       "use_flavours"))

        # Fallback
        self.assertEqual(cfg["trainings"]["fallback"]["target"],
                         common.get_training_attribute(training, "target"))

        # Inexistent
        self.assertIsNone(common.get_training_attribute(training, "hoppa"))

    def test_get_target_for_training(self):
        cfg = {
            "targets": {
                "MPD1": {
                    "device_root": "/mnt/mpd1"
                }
            },
            "trainings": {
                "T1": {
                    "target": "missing",
                },
                "T2": {
                    "target": "MPD1",
                }
            }
        }
        config = get_plugin_configuration(cfg)

        # No "targets" node
        no_targets_cfg = cfg.copy()
        del no_targets_cfg["targets"]
        no_targets_config = get_plugin_configuration(no_targets_cfg)
        training = no_targets_config["trainings"]["T1"]
        self.assertIsNone(common.get_target_for_training(training))

        # Undefined target
        training = config["trainings"]["T1"]
        self.assertIsNone(common.get_target_for_training(training))

        # Target found
        training = config["trainings"]["T2"]
        expected = config["targets"]["MPD1"].flatten()
        target = common.get_target_for_training(training).flatten()
        self.assertDictEqual(expected, target)

    def test_get_target_attribute_for_training(self):
        cfg = {
            "targets": {
                "MPD1": {
                    "device_root": "/mnt/mpd1"
                }
            },
            "trainings": {
                "T1": {
                    "target": "missing",
                },
                "T2": {
                    "target": "MPD1",
                }
            }
        }
        config = get_plugin_configuration(cfg)

        # Undefined target
        training = config["trainings"]["T1"]
        self.assertIsNone(common.get_target_attribute_for_training(training))

        # Get name (default param)
        training = config["trainings"]["T2"]
        expected = "MPD1"
        self.assertEqual(expected,
                         common.get_target_attribute_for_training(training))

        # Get name (using param)
        training = config["trainings"]["T2"]
        expected = "MPD1"
        self.assertEqual(expected,
                         common.get_target_attribute_for_training(training,
                                                                  "name"))

        # Get name (using param)
        training = config["trainings"]["T2"]
        expected = "/mnt/mpd1"
        self.assertEqual(expected,
                         common.get_target_attribute_for_training(training,
                                                                  "device_root"))

    def test_get_destination_path_for_training(self):
        tmpdir = self.create_temp_dir()
        tmpdir_slashed = "{}/".format(tmpdir)
        temp_sub_dir = os.path.join(tmpdir, "music")
        os.mkdir(temp_sub_dir)

        cfg = {
            "targets": {
                "MPD-no-device-root": {
                    "alias": "I have no device_root",
                    "device_path": "music"
                },
                "MPD-non-existent": {
                    "device_root": "/this/does/not/exist/i/hope",
                    "device_path": "music"
                },
                "MPD1": {
                    "device_root": tmpdir,
                    "device_path": "music"
                },
                "MPD2": {
                    "device_root": tmpdir_slashed,
                    "device_path": "music"
                },
                "MPD3": {
                    "device_root": tmpdir,
                    "device_path": "/music"
                },
                "MPD4": {
                    "device_root": tmpdir_slashed,
                    "device_path": "/music"
                },
                "MPD5": {
                    "device_root": tmpdir_slashed,
                    "device_path": "/music/"
                },
            },
            "trainings": {
                "T0-no-target": {
                    "alias": "I have no target",
                },
                "T0-no-device-root": {
                    "target": "MPD-no-device-root",
                },
                "T0-non-existent": {
                    "target": "MPD-non-existent",
                },
                "T1": {
                    "target": "MPD1",
                },
                "T2": {
                    "target": "MPD2",
                },
                "T3": {
                    "target": "MPD3",
                },
                "T4": {
                    "target": "MPD4",
                },
                "T5": {
                    "target": "MPD5",
                }
            }
        }
        config = get_plugin_configuration(cfg)

        # No target
        training = config["trainings"]["T0-no-target"]
        path = common.get_destination_path_for_training(training)
        self.assertIsNone(path)

        # No device_root in target
        training = config["trainings"]["T0-no-device-root"]
        path = common.get_destination_path_for_training(training)
        self.assertIsNone(path)

        # No non existent device_root in target
        training = config["trainings"]["T0-non-existent"]
        path = common.get_destination_path_for_training(training)
        self.assertIsNone(path)

        # No separators between root and path
        training = config["trainings"]["T1"]
        expected = os.path.realpath(util.normpath(
            os.path.join(tmpdir, "music")).decode())
        path = common.get_destination_path_for_training(training)
        self.assertEqual(expected, path)

        # final slash on device_root
        training = config["trainings"]["T2"]
        expected = os.path.realpath(util.normpath(
            os.path.join(tmpdir, "music")).decode())
        path = common.get_destination_path_for_training(training)
        self.assertEqual(expected, path)

        # leading slash on device path
        training = config["trainings"]["T3"]
        expected = os.path.realpath(util.normpath(
            os.path.join(tmpdir, "music")).decode())
        path = common.get_destination_path_for_training(training)
        self.assertEqual(expected, path)

        # final slash on device_root and leading slash on device path
        training = config["trainings"]["T4"]
        expected = os.path.realpath(util.normpath(
            os.path.join(tmpdir, "music")).decode())
        path = common.get_destination_path_for_training(training)
        self.assertEqual(expected, path)

        # slashes allover
        training = config["trainings"]["T5"]
        expected = os.path.realpath(util.normpath(
            os.path.join(tmpdir, "music")).decode())
        path = common.get_destination_path_for_training(training)
        self.assertEqual(expected, path)

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

        self.assertEqual("/media/mpd1/",
                         common.get_target_attribute(target, "device_root"))
        self.assertEqual("auto/",
                         common.get_target_attribute(target, "device_path"))
        self.assertEqual(None, common.get_target_attribute(target, "not_there"))

    def test_get_duration_of_items(self):
        items = [self.create_item(length=120), self.create_item(length=79)]
        self.assertEqual(199, common.get_duration_of_items(items))

        # ValueError
        baditem = self.create_item(length=-1)
        self.assertEqual(0, common.get_duration_of_items([baditem]))

        # ValueError
        baditem = self.create_item(length=None)
        self.assertEqual(0, common.get_duration_of_items([baditem]))

        # TypeError
        baditem = self.create_item(length=object())
        self.assertEqual(0, common.get_duration_of_items([baditem]))

    def test_get_min_max_sum_avg_for_items(self):
        item1 = self.create_item(mood_happy=100)
        item2 = self.create_item(mood_happy=150)
        item3 = self.create_item(mood_happy=200)
        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items(
            [item1, item2, item3], "mood_happy")
        self.assertEqual(100, _min)
        self.assertEqual(200, _max)
        self.assertEqual(450, _sum)
        self.assertEqual(150, _avg)

        item1 = self.create_item(mood_happy=99.7512345)
        item2 = self.create_item(mood_happy=150.482234)
        item3 = self.create_item(mood_happy=200.254733)
        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items(
            [item1, item2, item3], "mood_happy")
        self.assertEqual(99.751, _min)
        self.assertEqual(200.255, _max)
        self.assertEqual(450.488, _sum)
        self.assertEqual(150.163, _avg)

        # ValueError
        item1 = self.create_item(mood_happy=100)
        item2 = self.create_item(mood_happy="")
        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items(
            [item1, item2], "mood_happy")
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

        # empty list
        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items(
            [], "mood_happy")
        self.assertEqual(0, _min)
        self.assertEqual(0, _max)
        self.assertEqual(0, _sum)
        self.assertEqual(0, _avg)

    def test_increment_play_count_on_item(self):
        item1 = self.create_item(play_count=3)
        common.increment_play_count_on_item(item1, store=False, write=False)
        expected = 4
        self.assertEqual(expected, item1.get("play_count"))

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
