#  Copyright: Copyright (c) 2020., Adam Jakab
#  Author: Adam Jakab <adam at jakab dot pro>
#  License: See LICENSE.txt

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
