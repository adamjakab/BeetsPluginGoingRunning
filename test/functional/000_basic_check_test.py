#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 12:35 PM
#  License: See LICENSE.txt
#

from test.helper import TestHelper, Assertions, PLUGIN_NAME, PLUGIN_SHORT_DESCRIPTION, capture_log, capture_stdout


class BasicCheckTest(TestHelper, Assertions):
    """Test presence and invocation of the plugin.
    Only ensures that command does not fail.
    """

    def test_application(self):
        with capture_stdout() as out:
            self.runcli()

        self.assertIn(PLUGIN_NAME, out.getvalue())
        self.assertIn(PLUGIN_SHORT_DESCRIPTION, out.getvalue())

    def test_application_version(self):
        with capture_stdout() as out:
            self.runcli("version")

        self.assertIn("plugins: {0}".format(PLUGIN_NAME), out.getvalue())

    def test_plugin_no_arguments(self):
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME)

        self.assertIn("Usage: beet goingrunning [training] [options] [QUERY...]", out.getvalue())
