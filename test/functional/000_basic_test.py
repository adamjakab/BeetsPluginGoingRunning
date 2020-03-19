#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 12:35 PM
#  License: See LICENSE.txt
#

from test.helper import (
    FunctionalTestHelper, Assertions,
    PLUGIN_NAME, PLUGIN_SHORT_NAME, PLUGIN_SHORT_DESCRIPTION, get_single_line_from_output
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

    def test_with_core_plugin_acousticbrainz(self):
        """Flexible field type declaration conflict
        Introduced after release 1.1.1 when discovered core bug failing to compare flexible field types
        Ref.: https://beets.readthedocs.io/en/stable/dev/plugins.html#flexible-field-types
        This bug is present in beets version 1.4.9 so until the `item_types` declaration in the `GoingRunningPlugin`
        class is commented out this test will pass.
        Issue: https://github.com/adamjakab/BeetsPluginGoingRunning/issues/15
        Issue(Beets): https://github.com/beetbox/beets/issues/3520
        """
        extra_plugin = "acousticbrainz"
        self.reset_beets(config_file=b"empty.yml", extra_plugins=[extra_plugin])
        stdout = self.run_with_output("version")
        prefix = "plugins:"
        line = get_single_line_from_output(stdout, prefix)
        expected = "{0} {1}".format(prefix, ", ".join([extra_plugin, PLUGIN_NAME]))
        self.assertEqual(expected, line)
