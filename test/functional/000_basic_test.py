#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 12:35 PM
#  License: See LICENSE.txt
#

from test.helper import (
    FunctionalTestHelper, Assertions,
    PLUGIN_NAME, PLUGIN_SHORT_NAME, PLUGIN_SHORT_DESCRIPTION
)


class BasicTest(FunctionalTestHelper, Assertions):
    """Test presence and invocation of the plugin.
    Only ensures that command does not fail.
    """

    def test_application(self):
        stdout = self.run_with_output()
        self.assertIn(PLUGIN_NAME, stdout)
        self.assertIn(PLUGIN_SHORT_DESCRIPTION, stdout)

    def test_application_version(self):
        stdout = self.run_with_output("version")
        self.assertIn("plugins: {0}".format(PLUGIN_NAME), stdout)

    def test_plugin_no_arguments(self):
        self.reset_beets(config_file=b"empty.yml")
        stdout = self.run_with_output(PLUGIN_NAME)
        self.assertIn("Usage: beet goingrunning [training] [options] [QUERY...]", stdout)

    def test_plugin_shortname_no_arguments(self):
        self.reset_beets(config_file=b"empty.yml")
        stdout = self.run_with_output(PLUGIN_SHORT_NAME)
        self.assertIn("Usage: beet goingrunning [training] [options] [QUERY...]", stdout)
