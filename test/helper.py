#  Copyright: Copyright (c) 2020., Adam Jakab
#  Author: Adam Jakab <adam at jakab dot pro>
#  License: See LICENSE.txt
# References: https://docs.python.org/3/library/unittest.html
#

import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from random import randint, uniform
from unittest import TestCase

import beets
import six
import yaml
from beets import logging, library
from beets import plugins
from beets import ui
from beets import util
from beets.dbcore import types
from beets.library import Item
from beets.util import (
    syspath,
    bytestring_path,
    displayable_path,
)
from beets.util.confit import Subview, Dumper, LazyConfig, ConfigSource
from beetsplug import goingrunning
from beetsplug.goingrunning import common
from six import StringIO

# Values from about.py
PACKAGE_TITLE = common.plg_ns['__PACKAGE_TITLE__']
PACKAGE_NAME = common.plg_ns['__PACKAGE_NAME__']
PLUGIN_NAME = common.plg_ns['__PLUGIN_NAME__']
PLUGIN_ALIAS = common.plg_ns['__PLUGIN_ALIAS__']
PLUGIN_SHORT_DESCRIPTION = common.plg_ns['__PLUGIN_SHORT_DESCRIPTION__']
PLUGIN_VERSION = common.plg_ns['__version__']

_default_logger_name_ = 'beets.{plg}'.format(plg=PLUGIN_NAME)
logging.getLogger(_default_logger_name_).propagate = False


class LogCapture(logging.Handler):
    def __init__(self):
        super(LogCapture, self).__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(six.text_type(record.msg))


@contextmanager
def capture_log(logger=_default_logger_name_):
    """Capture Logger output
    >>> with capture_log() as logs:
    ...     log.info("Message")

    >>> full_log = ""\n"".join(logs)
    """
    capture = LogCapture()
    log = logging.getLogger(logger)
    log.addHandler(capture)
    try:
        yield capture.messages
    finally:
        log.removeHandler(capture)


@contextmanager
def capture_stdout():
    """Save stdout in a StringIO.
    >>> with capture_stdout() as output:
    ...     print('cseresznye')
    ...
    >>> output.getvalue()
    """
    org = sys.stdout
    sys.stdout = capture = StringIO()
    if six.PY2:  # StringIO encoding attr isn't writable in python >= 3
        sys.stdout.encoding = 'utf-8'
    try:
        yield sys.stdout
    finally:
        sys.stdout = org
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
    if six.PY2:  # StringIO encoding attr isn't writable in python >= 3
        sys.stdin.encoding = 'utf-8'
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
    """Separate a value from the logged output in the format of:
    prefix: value
    """
    prefix = "{}: {}".format(PLUGIN_NAME, prefix)
    value = None
    line = get_single_line_from_output(fulltext, prefix)
    # print("SL:{}".format(line))

    if prefix in line:
        value = line.replace(prefix, "")
        value = value.strip()

    return value


def _convert_args(args):
    """Convert args to bytestrings for Python 2 and convert them to strings
       on Python 3.
    """
    for i, elem in enumerate(args):
        if six.PY2:
            if isinstance(elem, six.text_type):
                args[i] = elem.encode(util.arg_encoding())
        else:
            if isinstance(elem, bytes):
                args[i] = elem.decode(util.arg_encoding())

    return args


def has_program(cmd, args=['--version']):
    """Returns `True` if `cmd` can be executed.
    """
    full_cmd = _convert_args([cmd] + args)
    try:
        with open(os.devnull, 'wb') as devnull:
            subprocess.check_call(full_cmd, stderr=devnull,
                                  stdout=devnull, stdin=devnull)
    except OSError:
        return False
    except subprocess.CalledProcessError:
        return False
    else:
        return True


class Assertions(object):
    def assertIsFile(self: TestCase, path):
        self.assertTrue(os.path.isfile(syspath(path)),
                        msg=u'Path is not a file: {0}'.format(
                            displayable_path(path)))


class BaseTestHelper(TestCase, Assertions):
    _tempdirs = []
    _tmpdir = None
    __item_count = 0

    default_item_values = {
        'title': u't\u00eftle {0}',
        'artist': u'the \u00e4rtist',
        'album': u'the \u00e4lbum',
        'track': 0,
        'format': 'MP3',
    }

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self._tmpdir = self.create_temp_dir()
        pass

    def tearDown(self):
        pass

    def create_item(self, **values):
        """Return an `Item` instance with sensible default values.

        The item receives its attributes from `**values` paratmeter. The
        `title`, `artist`, `album`, `track`, `format` and `path`
        attributes have defaults if they are not given as parameters.
        The `title` attribute is formatted with a running item count to
        prevent duplicates.
        """
        item_count = self._get_item_count()
        _values = self.default_item_values
        _values['title'] = _values['title'].format(item_count)
        _values['track'] = item_count
        _values.update(values)
        item = Item(**_values)

        return item

    def _get_item_count(self):
        self.__item_count += 1
        return self.__item_count

    def create_temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        self._tempdirs.append(temp_dir)
        return temp_dir


class UnitTestHelper(BaseTestHelper):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        beets.ui._configure({"verbose": True})

    def setUp(self):
        super().setUp()
        self.__item_count = 0

    def create_multiple_items(self, count=10, **values):
        items = []
        for i in range(count):
            new_values = values.copy()
            for key in values:
                if type(values[key]) == list and len(values[key]) == 2:
                    if type(values[key][0]) == float or type(
                            values[key][1]) == float:
                        random_val = uniform(values[key][0], values[key][1])
                    elif type(values[key][0]) == int and type(
                            values[key][1]) == int:
                        random_val = randint(values[key][0], values[key][1])
                    else:
                        raise ValueError("Elements for key({}) are neither float nor int!")

                    new_values[key] = random_val
            items.append(self.create_item(**new_values))

        return items


class FunctionalTestHelper(BaseTestHelper):
    _test_config_dir_ = os.path.join(bytestring_path(
        os.path.dirname(__file__)), b'config')

    _test_fixture_dir = os.path.join(bytestring_path(
        os.path.dirname(__file__)), b'fixtures')

    beetsdir = None
    __item_count = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._CFG = cls._get_default_CFG()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        """Setup before each test
        """
        super().setUp()
        self.beetsdir = bytestring_path(self._tmpdir)
        os.environ['BEETSDIR'] = self.beetsdir.decode()

    def tearDown(self):
        """Tear down after each test
        """
        super().tearDown()
        self._teardown_beets()
        self._CFG = self._get_default_CFG()

    def setup_beets(self, cfg=None):
        if cfg is not None and type(cfg) is dict:
            self._CFG.update(cfg)

        plugins._classes = {self._CFG["plugin"]}
        if self._CFG["extra_plugins"]:
            plugins.load_plugins(self._CFG["extra_plugins"])

        # copy configuration file to beets dir
        config_file = os.path.join(self._test_config_dir_,
                                   self._CFG["config_file"]).decode()
        file_list = [{'file_name': 'config.yaml', 'file_path': config_file}]
        self._copy_files_to_beetsdir(file_list)

        self.config = beets.config
        self.config.clear()
        self.config.read()

        self.config['plugins'] = []
        self.config['verbose'] = True
        self.config['ui']['color'] = False
        self.config['threaded'] = False
        self.config['import']['copy'] = False

        self.config['directory'] = self.beetsdir.decode()
        self.lib = beets.library.Library(':memory:', self.beetsdir.decode())

        # This will initialize the plugins
        plugins.find_plugins()

    def _teardown_beets(self):
        self.unload_plugins()

        # reset types updated here: beets/ui/__init__.py:1148
        library.Item._types = {'data_source': types.STRING}

        # Clean temporary folders
        for tempdir in self._tempdirs:
            if os.path.exists(tempdir):
                shutil.rmtree(syspath(tempdir), ignore_errors=True)
        self._tempdirs = []

        if hasattr(self, 'lib'):
            if hasattr(self.lib, '_connections'):
                del self.lib._connections

        if 'BEETSDIR' in os.environ:
            del os.environ['BEETSDIR']

        self.config.clear()

    def ensure_training_target_path(self, training_name):
        """Make sure that the path set withing the target for the training
        exists by creating it under the temporary folder and changing the
        device_root key in the configuration
        """
        target_name = self.config[PLUGIN_NAME]["trainings"][training_name][
            "target"].get()
        target = self.config[PLUGIN_NAME]["targets"][target_name]
        device_root = self.create_temp_dir()
        device_path = target["device_path"].get()
        target["device_root"].set(device_root)
        full_path = os.path.join(device_root, device_path)
        os.makedirs(full_path)

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

    def run_with_log_capture(self, *args):
        with capture_log() as out:
            self.run_command(*args)
        return util.text_string("\n".join(out))

    def _get_item_count(self):
        """Internal counter for create_item
        """
        self.__item_count += 1
        return self.__item_count

    def create_item(self, **values):
        """... The item is attached to the database from `self.lib`.
        """
        values['db'] = self.lib
        item = super().create_item(**values)
        # print("Creating Item: {}".format(values_))

        if 'path' not in values:
            item['path'] = 'test/fixtures/song.' + item['format'].lower()

        # mtime needs to be set last since other assignments reset it.
        item.mtime = 12345

        return item

    def add_single_item_to_library(self, **values):
        item = self.create_item(**values)
        item.add(self.lib)
        item.store()

        # item.move(MoveOperation.COPY)
        return item

    def add_multiple_items_to_library(self, count=10, **values):
        for i in range(count):
            new_values = values.copy()
            for key in values:
                if type(values[key]) == list and len(values[key]) == 2:
                    if type(values[key][0]) == float or type(
                            values[key][1]) == float:
                        random_val = uniform(values[key][0], values[key][1])
                    elif type(values[key][0]) == int and type(
                            values[key][1]) == int:
                        random_val = randint(values[key][0], values[key][1])
                    else:
                        raise ValueError(
                            "Elements for key({}) are neither float nor int!")

                    new_values[key] = random_val
            self.add_single_item_to_library(**new_values)

    def _copy_files_to_beetsdir(self, file_list: list):
        if file_list:
            for file in file_list:
                if isinstance(file, dict) and \
                        'file_name' in file and 'file_path' in file:
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
                shutil.copyfile(src, dst)

    @staticmethod
    def _dump_config(cfg: Subview):
        flat = cfg.flatten()
        print(yaml.dump(flat, Dumper=Dumper, default_flow_style=None,
                        indent=2, width=1000))

    @staticmethod
    def unload_plugins():
        for plugin in plugins._classes:
            plugin.listeners = None
            plugins._classes = set()
            plugins._instances = {}

    @staticmethod
    def _get_default_CFG():
        return {
            'plugin': goingrunning.GoingRunningPlugin,
            'config_file': b'default.yml',
            'extra_plugins': [],
        }
