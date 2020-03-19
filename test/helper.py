#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/18/20, 12:31 AM
#  License: See LICENSE.txt
#
# References: https://docs.python.org/3/library/unittest.html
#

import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from random import randint, uniform
from unittest import TestCase

import beets
import six
import yaml
from beets import logging
from beets import plugins
from beets import ui
from beets import util
from beets.library import Item
from beets.util import (
    syspath,
    bytestring_path,
    displayable_path,
)
from beets.util.confit import Subview, Dumper, LazyConfig, ConfigSource
from six import StringIO

from beetsplug import goingrunning

# Values
PLUGIN_NAME = u'goingrunning'
PLUGIN_SHORT_NAME = u'run'
PLUGIN_SHORT_DESCRIPTION = u'run with the music that matches your training sessions'


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
    # if suppress_output:
    # Is this too violent?
    # log.handlers = []
    log.addHandler(capture)
    try:
        yield capture.messages
    finally:
        log.removeHandler(capture)


@contextmanager
def capture_stdout():
    """Save stdout in a StringIO.
    >>> with capture_stdout() as output:
    ...     print('spam')
    ...
    >>> output.getvalue()
    """
    orig = sys.stdout
    sys.stdout = capture = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = orig
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


def get_plugin_configuration(cfg):
    """Creates and returns a configuration from a dict to play around with"""
    config = LazyConfig("unittest")
    cfg = {PLUGIN_NAME: cfg}
    config.add(ConfigSource(cfg))
    return config[PLUGIN_NAME]


def get_single_line_from_output(text: str, prefix: str):
    selected_line = ""
    lines = text.split("\n")
    for line in lines:
        if prefix in line:
            selected_line = line
            break

    return selected_line


def convert_time_to_seconds(time: str):
    return sum(x * int(t) for x, t in zip([3600, 60, 1], time.split(":")))


def get_value_separated_from_output(fulltext: str, prefix: str):
    """Separate the value that has been printed to the stdout in the format of:
    prefix: value
    """
    value = None
    line = get_single_line_from_output(fulltext, prefix)
    # print("SL:{}".format(line))

    if prefix in line:
        value = line.replace(prefix, "")
        value = value.strip()

    return value


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


class UnitTestHelper(TestCase, Assertions):
    __item_count = 0

    def create_item(self, **values):
        """Return an `Item` instance with sensible default values.

        The item receives its attributes from `**values` paratmeter. The
        `title`, `artist`, `album`, `track`, `format` and `path`
        attributes have defaults if they are not given as parameters.
        The `title` attribute is formatted with a running item count to
        prevent duplicates.
        """
        item_count = self._get_item_count()
        values_ = {
            'title': u't\u00eftle {0}',
            'artist': u'the \u00e4rtist',
            'album': u'the \u00e4lbum',
            'track': item_count,
            'format': 'MP3',
        }
        values_.update(values)

        values_['title'] = values_['title'].format(item_count)
        item = Item(**values_)

        return item

    def create_multiple_items(self, count=10, **values):
        items = []
        for i in range(count):
            new_values = values.copy()
            for key in values:
                if type(values[key]) == list and len(values[key]) == 2:
                    if type(values[key][0]) == float or type(values[key][1]) == float:
                        random_val = uniform(values[key][0], values[key][1])
                    elif type(values[key][0]) == int and type(values[key][1]) == int:
                        random_val = randint(values[key][0], values[key][1])
                    else:
                        raise ValueError("Elements for key({}) are neither float nor int!")

                    new_values[key] = random_val
            items.append(self.create_item(**new_values))

        return items

    def _get_item_count(self):
        self.__item_count += 1
        return self.__item_count


class FunctionalTestHelper(TestCase, Assertions):
    _test_config_dir_ = os.path.join(bytestring_path(os.path.dirname(__file__)), b'config')
    _test_fixture_dir = os.path.join(bytestring_path(os.path.dirname(__file__)), b'fixtures')
    _test_target_dir = bytestring_path("/tmp/beets-goingrunning-test-drive")
    __item_count = 0

    def setUp(self):
        """Setup before running any tests with an empty configuration file.
        """
        self.reset_beets(config_file=b"default.yml")

    def tearDown(self):
        self.teardown_beets()

    def reset_beets(self, config_file: bytes, extra_plugins=None, beet_files: list = None):
        self.teardown_beets()
        plugins._classes = {goingrunning.GoingRunningPlugin}
        if extra_plugins:
            plugins.load_plugins(extra_plugins)

        self._setup_beets(config_file, beet_files)

    def _setup_beets(self, config_file: bytes, beet_files: list = None):
        self.addCleanup(self.teardown_beets)
        self.beetsdir = bytestring_path(self.create_temp_dir())
        os.environ['BEETSDIR'] = self.beetsdir.decode()

        # copy configuration file to beets dir
        config_file = os.path.join(self._test_config_dir_, config_file).decode()
        file_list = [{'file_name': 'config.yaml', 'file_path': config_file}]
        self._copy_files_to_beetsdir(file_list)

        # copy additional files to beets dir (
        self._copy_files_to_beetsdir(beet_files)

        self.config = beets.config
        self.config.clear()
        self.config.read()

        self.config['plugins'] = []
        self.config['verbose'] = True
        self.config['ui']['color'] = False
        self.config['threaded'] = False
        self.config['import']['copy'] = False

        os.makedirs(self._test_target_dir, exist_ok=True)
        self.config['directory'] = self.beetsdir.decode()
        self.lib = beets.library.Library(':memory:', self.beetsdir.decode())

        # This will initialize the plugins
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
                # print("Copy({}) to beetsdir: {}".format(src, file_name))

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

    def create_temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        self._tempdirs.append(temp_dir)
        return temp_dir

    def ensure_training_target_path(self, training_name):
        # Set existing path for target
        target_name = self.config[PLUGIN_NAME]["trainings"][training_name]["target"].get()
        target = self.config[PLUGIN_NAME]["targets"][target_name]
        device_root = self.create_temp_dir()
        device_path = target["device_path"].get()
        target["device_root"].set(device_root)
        full_path = os.path.join(device_root, device_path)
        os.makedirs(full_path)

    @staticmethod
    def unload_plugins():
        for plugin in plugins._classes:
            plugin.listeners = None
            plugins._classes = set()
            plugins._instances = {}

    # def runcli(self, *args):
    #     # TODO mock stdin
    #     with capture_stdout() as out:
    #         try:
    #             ui._raw_main(_convert_args(list(args)), self.lib)
    #         except ui.UserError as u:
    #             # TODO remove this and handle exceptions in tests
    #             print(u.args[0])
    #     return out.getvalue()

    def run_command(self, *args, **kwargs):
        """Run a beets command with an arbitrary amount of arguments. The
           Library` defaults to `self.lib`, but can be overridden with
           the keyword argument `lib`.
        """
        sys.argv = ['beet']  # avoid leakage from test suite args
        lib = None
        if hasattr(self, 'lib'):
            lib = self.lib
        lib = kwargs.get('lib', lib)
        beets.ui._raw_main(_convert_args(list(args)), lib)

    def run_with_output(self, *args):
        with capture_stdout() as out:
            self.run_command(*args)
        return util.text_string(out.getvalue())

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

    def _get_item_count(self):
        """Internal counter for create_item
        """
        self.__item_count += 1
        return self.__item_count

    def create_item(self, **values):
        """Return an `Item` instance with sensible default values.

        The item receives its attributes from `**values` paratmeter. The
        `title`, `artist`, `album`, `track`, `format` and `path`
        attributes have defaults if they are not given as parameters.
        The `title` attribute is formated with a running item count to
        prevent duplicates. The default for the `path` attribute
        respects the `format` value.

        The item is attached to the database from `self.lib`.
        """
        item_count = self._get_item_count()
        values_ = {
            'title': u't\u00eftle {0}',
            'artist': u'the \u00e4rtist',
            'album': u'the \u00e4lbum',
            'track': item_count,
            'format': 'MP3',
        }
        values_.update(values)
        values_['title'] = values_['title'].format(item_count)

        # print("Creating Item: {}".format(values_))

        values_['db'] = self.lib
        item = Item(**values_)

        if 'path' not in values:
            item['path'] = 'test/fixtures/song.' + item['format'].lower()

        # mtime needs to be set last since other assignments reset it.
        item.mtime = 12345

        return item

    def add_single_item_to_library(self, **values):
        item = self.create_item(**values)
        # item = Item.from_path(self.get_fixture_item_path(values.pop('format')))
        item.add(self.lib)
        # item.move(MoveOperation.COPY)
        # item.write()
        return item

    def add_multiple_items_to_library(self, count=10, **values):
        for i in range(count):
            new_values = values.copy()
            for key in values:
                if type(values[key]) == list and len(values[key]) == 2:
                    if type(values[key][0]) == float or type(values[key][1]) == float:
                        random_val = uniform(values[key][0], values[key][1])
                    elif type(values[key][0]) == int and type(values[key][1]) == int:
                        random_val = randint(values[key][0], values[key][1])
                    else:
                        raise ValueError("Elements for key({}) are neither float nor int!")

                    new_values[key] = random_val
            self.add_single_item_to_library(**new_values)
