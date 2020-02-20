#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 5:44 PM
#  License: See LICENSE.txt
#

from beets.util.confit import Subview

from test.helper import TestHelper, Assertions, PLUGIN_NAME, capture_stdout


class BasicCommandTest(TestHelper, Assertions):

    def test_training_listing_long(self):
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "--list")

        self.assertIn("You have not created any trainings yet.", out.getvalue())

    def test_training_listing_short(self):
        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "-l")

        self.assertIn("You have not created any trainings yet.", out.getvalue())

    def test_training_listing(self):
        self.reset_beets(config_file=b"config_user.yml")

        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "--list")

        output = out.getvalue()
        self.assertIn("::: training-1", output)
        self.assertIn("::: training-2", output)
        self.assertIn("::: marathon", output)


    def test_training_handling(self):
        self.reset_beets(config_file=b"config_user.yml")

        with capture_stdout() as out:
            self.runcli(PLUGIN_NAME, "marathon")

        self.assertTrue(True)
