#  Copyright: Copyright (c) 2020., Adam Jakab
#  Author: Adam Jakab <adam at jakab dot pro>
#  License: See LICENSE.txt

from beets.util.confit import Subview
from beetsplug.goingrunning import GoingRunningCommand
from beetsplug.goingrunning import command

from test.helper import UnitTestHelper, get_plugin_configuration, \
    PLUGIN_NAME, PLUGIN_ALIAS, PLUGIN_SHORT_DESCRIPTION


class CommandTest(UnitTestHelper):
    """Test methods in the beetsplug.goingrunning.command module
    """

    def test_module_values(self):
        self.assertEqual(u'goingrunning', PLUGIN_NAME)
        self.assertEqual(u'run', PLUGIN_ALIAS)
        self.assertEqual(
            u'run with the music that matches your training sessions',
            PLUGIN_SHORT_DESCRIPTION)

    def test_class_init_config(self):
        cfg = {"something": "good"}
        config = get_plugin_configuration(cfg)
        inst = command.GoingRunningCommand(config)
        self.assertEqual(config, inst.config)

    def test_gather_query_elements__test_1(self):
        plg_cfg: Subview = self.config["goingrunning"]
        training: Subview = plg_cfg["trainings"]["q-test-1"]
        cmd = GoingRunningCommand(plg_cfg)
        elements = cmd._gather_query_elements(training)
        self.assertListEqual([], elements)

    def test_gather_query_elements__test_2(self):
        plg_cfg: Subview = self.config["goingrunning"]
        training: Subview = plg_cfg["trainings"]["q-test-2"]
        cmd = GoingRunningCommand(plg_cfg)
        elements = cmd._gather_query_elements(training)
        expected = ['bpm:100..150', 'length:120..300', 'genre:hard rock']
        self.assertListEqual(expected, elements)

    def test_gather_query_elements__test_3(self):
        plg_cfg: Subview = self.config["goingrunning"]
        training: Subview = plg_cfg["trainings"]["q-test-3"]
        cmd = GoingRunningCommand(plg_cfg)
        elements = cmd._gather_query_elements(training)
        expected = ['bpm:100..150', 'length:120..300', 'genre:reggae']
        self.assertListEqual(expected, elements)

    def test_gather_query_elements__test_4(self):
        plg_cfg: Subview = self.config["goingrunning"]
        training: Subview = plg_cfg["trainings"]["q-test-4"]
        cmd = GoingRunningCommand(plg_cfg)
        elements = cmd._gather_query_elements(training)
        expected = ['bpm:100..150', 'year:2015..',
                    'genre:reggae', 'year:1960..1969']
        self.assertListEqual(expected, elements)

    def test_gather_query_elements__test_4_bis(self):
        """Command line query should always be the first in the list
        """
        plg_cfg: Subview = self.config["goingrunning"]
        training: Subview = plg_cfg["trainings"]["q-test-4"]
        cmd = GoingRunningCommand(plg_cfg)
        cmd.query = ['albumartist:various artists']
        elements = cmd._gather_query_elements(training)
        expected = cmd.query + \
                   ['bpm:100..150', 'year:2015..',
                    'genre:reggae', 'year:1960..1969']
        self.assertListEqual(expected, elements)

    def test_gather_query_elements__test_5(self):
        plg_cfg: Subview = self.config["goingrunning"]
        training: Subview = plg_cfg["trainings"]["q-test-5"]
        cmd = GoingRunningCommand(plg_cfg)
        elements = cmd._gather_query_elements(training)
        expected = ['genre:rock', 'genre:blues', 'genre:ska',
                    'genre:funk', 'genre:Rockabilly', 'genre:Disco']
        self.assertListEqual(expected, elements)
