#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/18/20, 12:31 AM
#  License: See LICENSE.txt
#
# References: https://docs.python.org/3/library/unittest.html
#
import json
import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from random import randint
from unittest import TestCase

import beets
import six
import yaml
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
from beets.util.confit import Subview, Dumper
from six import StringIO

from beetsplug import goingrunning

# Values
PLUGIN_NAME = 'goingrunning'
PLUGIN_SHORT_DESCRIPTION = 'bring some music with you that matches your training'


class LogCapture(logging.Handler):

    def __init__(self):
        super(LogCapture, self).__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(six.text_type(record.msg))


@contextmanager
def capture_log(logger='beets', suppress_output=True):
    """Capture Logger output
        with capture_log() as logs:
            log.info(msg)
        full_log = '\n'.join(logs)
    """
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
    orig = sys.stdout
    sys.stdout = capture = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = orig
        # if not suppress_output:
        print(capture.getvalue())


@contextmanager
def control_stdin(userinput=None):
    """Sends ``input`` to stdin.
    >>> with control_stdin('yes'):
    ...     input()
    'yes'
    """
    org = sys.stdin
    sys.stdin = StringIO(userinput)
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
    _test_config_dir_ = os.path.join(bytestring_path(os.path.dirname(__file__)), b'config')
    _test_fixture_dir = os.path.join(bytestring_path(os.path.dirname(__file__)), b'fixtures')
    _test_target_dir = bytestring_path("/tmp/beets-goingrunning-test-drive")

    def setUp(self):
        """Setup before running any tests.
        """
        self.reset_beets(config_file=b"empty.yml")

    def tearDown(self):
        self.teardown_beets()

    def reset_beets(self, config_file: bytes, beet_files: list = None):
        self.teardown_beets()
        plugins._classes = {goingrunning.GoingRunningPlugin}
        self._setup_beets(config_file, beet_files)

    def _setup_beets(self, config_file: bytes, beet_files: list = None):
        self.addCleanup(self.teardown_beets)
        self.beetsdir = bytestring_path(self.mkdtemp())
        os.environ['BEETSDIR'] = self.beetsdir.decode()

        self.config = beets.config
        self.config.clear()

        # copy additional files to beets dir (
        self._copy_files_to_beetsdir(beet_files)

        # copy configuration file to beets dir
        config_file = os.path.join(self._test_config_dir_, config_file).decode()
        file_list = [{'file_name': 'config.yaml', 'file_path': config_file}]
        self._copy_files_to_beetsdir(file_list)

        self.config.read()

        self.config['plugins'] = []
        self.config['verbose'] = True
        self.config['ui']['color'] = False
        self.config['threaded'] = False
        self.config['import']['copy'] = False

        os.makedirs(self._test_target_dir, exist_ok=True)

        self.config['directory'] = self.beetsdir.decode()

        self.lib = beets.library.Library(':memory:', self.beetsdir.decode())

        # This will initialize (create instance) of the plugins
        plugins.find_plugins()

    def _copy_files_to_beetsdir(self, file_list: list):
        if file_list:
            for file in file_list:
                if isinstance(file, dict) and 'file_name' in file and 'file_path' in file:
                    src = file['file_path']
                    file_name = file['file_name']
                else:
                    src = file
                    file_name = os.path.basename(src)

                if isinstance(src, bytes):
                    src = src.decode()

                if isinstance(file_name, bytes):
                    file_name = file_name.decode()

                dst = os.path.join(self.beetsdir.decode(), file_name)
                print("Copy to beetsdir: {}".format(file_name))

                shutil.copyfile(src, dst)

    def teardown_beets(self):
        self.unload_plugins()

        shutil.rmtree(self._test_target_dir, ignore_errors=True)

        if hasattr(self, '_tempdirs'):
            for tempdir in self._tempdirs:
                if os.path.exists(tempdir):
                    shutil.rmtree(syspath(tempdir), ignore_errors=True)
        self._tempdirs = []

        if hasattr(self, 'lib'):
            if hasattr(self.lib, '_connections'):
                del self.lib._connections

        if 'BEETSDIR' in os.environ:
            del os.environ['BEETSDIR']

        if hasattr(self, 'config'):
            self.config.clear()

        # beets.config.read(user=False, defaults=True)

    def mkdtemp(self):
        path = tempfile.mkdtemp()
        self._tempdirs.append(path)
        return path

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
        return os.path.join(self.beetsdir, path.replace(b'/', bytestring_path(os.sep)))

    @staticmethod
    def _dump_config(cfg: Subview):
        # print(json.dumps(cfg.get(), indent=4, sort_keys=False))
        flat = cfg.flatten()
        print(yaml.dump(flat, Dumper=Dumper, default_flow_style=None, indent=2, width=1000))

    def get_fixture_item_path(self, ext):
        assert (ext in 'mp3 m4a ogg'.split())
        return os.path.join(self._test_fixture_dir, bytestring_path('song.' + ext.lower()))

    def add_multiple_items_to_library(self, count=10, song_bpm=None, song_length=None, **kwargs):
        if song_bpm is None:
            song_bpm = [60, 220]
        if song_length is None:
            song_length = [15, 300]
        for i in range(count):
            bpm = randint(song_bpm[0], song_bpm[1])
            length = randint(song_length[0], song_length[1])
            self.add_single_item_to_library(bpm=bpm, length=length, **kwargs)

    def add_single_item_to_library(self, **kwargs):
        values = {
            'title': 'track 1',
            'artist': 'artist 1',
            'album': 'album 1',
            'bpm': randint(120, 180),
            'length': randint(90, 720),
            'format': 'mp3',
        }
        values.update(kwargs)
        item = Item.from_path(self.get_fixture_item_path(values.pop('format')))
        item.update(values)
        item.add(self.lib)
        item.move(MoveOperation.COPY)
        item.write()
        return item


