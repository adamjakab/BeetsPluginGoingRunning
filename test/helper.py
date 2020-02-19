#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/18/20, 12:31 AM
#  License: See LICENSE.txt
#

import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from unittest import TestCase

import beets
import six
from beets import logging
from beets import plugins
from beets import ui
from beets import util
from beets.library import Item
# from beets.mediafile import MediaFile
from beets.util import (
    MoveOperation,
    syspath,
    bytestring_path,
    displayable_path,
)
from six import StringIO

from beetsplug import goingrunning

logging.getLogger('beets').propagate = True


class LogCapture(logging.Handler):

    def __init__(self):
        super(LogCapture, self).__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(six.text_type(record.msg))


@contextmanager
def capture_log(logger='beets', suppress_output=True):
    capture = LogCapture()
    log = logging.getLogger(logger)
    log.propagate = True
    if suppress_output:
        # Is this too violent?
        log.handlers = []
    log.addHandler(capture)
    try:
        yield capture.messages
    finally:
        log.removeHandler(capture)


@contextmanager
def capture_stdout(suppress_output=True):
    """Save stdout in a StringIO.
    >>> with capture_stdout() as output:
    ...     print('spam')
    ...
    >>> output.getvalue()
    'spam'
    """
    org = sys.stdout
    sys.stdout = capture = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = org
        #if not suppress_output:
        print(capture.getvalue())


@contextmanager
def control_stdin(input=None):
    """Sends ``input`` to stdin.
    >>> with control_stdin('yes'):
    ...     input()
    'yes'
    """
    org = sys.stdin
    sys.stdin = StringIO(input)
    try:
        yield sys.stdin
    finally:
        sys.stdin = org


def _convert_args(args):
    """Convert args to strings
    """
    for i, elem in enumerate(args):
        if isinstance(elem, bytes):
            args[i] = elem.decode(util.arg_encoding())

    return args


class Assertions(object):
    def assertIsFile(self: TestCase, path):
        self.assertTrue(os.path.isfile(syspath(path)),
                        msg=u'Path is not a file: {0}'.format(displayable_path(path)))


class TestHelper(TestCase, Assertions):

    def setUp(self):
        """Setup required for running test. Must be called before running any tests.
        """

        self._tempdirs = []
        plugins._classes = {goingrunning.GoingRunningPlugin}
        self.setup_beets()

    def tearDown(self):
        self.unload_plugins()
        for tempdir in self._tempdirs:
            shutil.rmtree(syspath(tempdir))

    def mkdtemp(self):
        # This return a str path, i.e. Unicode on Python 3. We need this in
        # order to put paths into the configuration.
        path = tempfile.mkdtemp()
        self._tempdirs.append(path)
        return path

    def setup_beets(self):
        self.addCleanup(self.teardown_beets)
        os.environ['BEETSDIR'] = self.mkdtemp()

        self.config = beets.config
        self.config.clear()
        self.config.read()

        self.config['plugins'] = []
        self.config['verbose'] = True
        self.config['ui']['color'] = False
        self.config['threaded'] = False
        self.config['import']['copy'] = False

        libdir = self.mkdtemp()
        self.config['directory'] = libdir
        self.libdir = bytestring_path(libdir)

        self.lib = beets.library.Library(':memory:', self.libdir)
        self.fixture_dir = os.path.join(
            bytestring_path(os.path.dirname(__file__)),
            b'fixtures')

        self.IMAGE_FIXTURE1 = os.path.join(self.fixture_dir,
                                           b'image.png')
        self.IMAGE_FIXTURE2 = os.path.join(self.fixture_dir,
                                           b'image_black.png')

        # This will initialize (create instance) of the plugins
        plugins.find_plugins()


    def teardown_beets(self):
        del self.lib._connections
        if 'BEETSDIR' in os.environ:
            del os.environ['BEETSDIR']
        self.config.clear()
        beets.config.read(user=False, defaults=True)

    def set_paths_config(self, conf):
        self.lib.path_formats = conf.items()

    @staticmethod
    def unload_plugins():
        for plugin in plugins._classes:
            plugin.listeners = None
            plugins._classes = set()
            plugins._instances = {}

    def runcli(self, *args):
        # TODO mock stdin
        with capture_stdout() as out:
            try:
                ui._raw_main(_convert_args(list(args)), self.lib)
            except ui.UserError as u:
                # TODO remove this and handle exceptions in tests
                print(u.args[0])
        return out.getvalue()

    def lib_path(self, path):
        return os.path.join(self.libdir,
                            path.replace(b'/', bytestring_path(os.sep)))

    def item_fixture_path(self, fmt):
        assert (fmt in 'mp3 m4a ogg'.split())
        return os.path.join(self.fixture_dir,
                            bytestring_path('min.' + fmt.lower()))
