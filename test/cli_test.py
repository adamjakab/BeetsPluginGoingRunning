#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/17/20, 10:53 PM
#  License: See LICENSE.txt
#

from unittest import TestCase

from test.helper import TestHelper

from beets import config as beets_global_config

from beetsplug import goingrunning


class CompletionTest(TestHelper):
    """Test invocation of ``beet goingrunning`` with this plugin.
    Only ensures that command does not fail.
    """

    def test_completion(self):
        self.runcli('goingrunning')


class TestBase(TestCase):

    def test_something(self):
        self.assertEqual(True, True)

    def test_human_readable_time(self):
        s = goingrunning.get_human_readable_time(0)
        self.assertEqual(s, "0:00:00", "Bad Time!")

    def test_get_beets_global_config(self):
        beets_cfg = beets_global_config
        plg_cfg = goingrunning.get_beets_global_config()
        self.assertEqual(beets_cfg, plg_cfg)


