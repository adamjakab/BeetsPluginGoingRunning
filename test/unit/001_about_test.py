#  Copyright: Copyright (c) 2020., Adam Jakab
#  Author: Adam Jakab <adam at jakab dot pro>
#  License: See LICENSE.txt

from beetsplug.goingrunning import about

from test.helper import UnitTestHelper, PACKAGE_TITLE, PACKAGE_NAME, \
    PLUGIN_NAME, PLUGIN_ALIAS, PLUGIN_SHORT_DESCRIPTION, PLUGIN_VERSION


class AboutTest(UnitTestHelper):
    """Test values defined in the beetsplug.goingrunning.about module
    """

    def test_author(self):
        attr = "__author__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))

    def test_email(self):
        attr = "__email__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))

    def test_copyright(self):
        attr = "__copyright__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))

    def test_license(self):
        attr = "__license__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))

    def test_version(self):
        attr = "__version__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))
        self.assertEqual(PLUGIN_VERSION, getattr(about, attr))

    def test_status(self):
        attr = "__status__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))

    def test_package_title(self):
        attr = "__PACKAGE_TITLE__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))
        self.assertEqual(PACKAGE_TITLE, getattr(about, attr))

    def test_package_name(self):
        attr = "__PACKAGE_NAME__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))
        self.assertEqual(PACKAGE_NAME, getattr(about, attr))

    def test_package_description(self):
        attr = "__PACKAGE_DESCRIPTION__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))

    def test_package_url(self):
        attr = "__PACKAGE_URL__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))

    def test_plugin_name(self):
        attr = "__PLUGIN_NAME__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))
        self.assertEqual(PLUGIN_NAME, getattr(about, attr))

    def test_plugin_alias(self):
        attr = "__PLUGIN_ALIAS__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))
        self.assertEqual(PLUGIN_ALIAS, getattr(about, attr))

    def test_plugin_short_description(self):
        attr = "__PLUGIN_SHORT_DESCRIPTION__"
        self.assertTrue(hasattr(about, attr))
        self.assertIsNotNone(getattr(about, attr))
        self.assertEqual(PLUGIN_SHORT_DESCRIPTION, getattr(about, attr))
