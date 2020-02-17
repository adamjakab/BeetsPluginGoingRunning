#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/17/20, 10:53 PM
#  License: See LICENSE.txt
#

from unittest import TestCase

from beetsplug import goingrunning


class TestBase(TestCase):

    def test_something(self):
        self.assertEqual(True, True)

    def test_human_readable_time(self):
        s = goingrunning.get_human_readable_time(0)
        self.assertEqual(s, "0:00:00", "Bad Time!")



