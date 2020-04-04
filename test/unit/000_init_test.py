#  Copyright: Copyright (c) 2020., Adam Jakab
#  Author: Adam Jakab <adam at jakab dot pro>
#  License: See LICENSE.txt

from beets.dbcore import types
from beetsplug.goingrunning import GoingRunningPlugin
from beetsplug.goingrunning.command import GoingRunningCommand

from test.helper import UnitTestHelper, PLUGIN_NAME


class PluginTest(UnitTestHelper):
    """Test methods in the beetsplug.goingrunning module
    """

    def test_plugin(self):
        plg = GoingRunningPlugin()
        self.assertEqual(PLUGIN_NAME, plg.name)

    def test_plugin_commands(self):
        plg = GoingRunningPlugin()
        GRC = plg.commands()[0]
        self.assertIsInstance(GRC, GoingRunningCommand)

    def test_plugin_types_definitions(self):
        plg = GoingRunningPlugin()
        definitions = {'play_count': types.INTEGER}
        self.assertDictEqual(definitions, plg.item_types)
