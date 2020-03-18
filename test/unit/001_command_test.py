#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 3/17/20, 7:09 PM
#  License: See LICENSE.txt
#
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 3/17/20, 3:28 PM
#  License: See LICENSE.txt
#

from test.helper import UnitTestHelper, Assertions, get_plugin_configuration
from beetsplug.goingrunning import command

from logging import Logger


class CommandTest(UnitTestHelper, Assertions):
    """Test methods in the beetsplug.goingrunning.command module
    """

    def test_module_values(self):
        self.assertTrue(hasattr(command, "__PLUGIN_NAME__"))
        self.assertTrue(hasattr(command, "__PLUGIN_SHORT_NAME__"))
        self.assertTrue(hasattr(command, "__PLUGIN_SHORT_DESCRIPTION__"))

        self.assertEqual(u'goingrunning', command.__PLUGIN_NAME__)
        self.assertEqual(u'run', command.__PLUGIN_SHORT_NAME__)
        self.assertEqual(u'run with the music that matches your training sessions',
                         command.__PLUGIN_SHORT_DESCRIPTION__)

    def test_class_init_config(self):
        cfg = {"something": "good"}
        config = get_plugin_configuration(cfg)
        inst = command.GoingRunningCommand(config)
        self.assertEqual(config, inst.config)
