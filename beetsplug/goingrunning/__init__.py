#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 11:30 AM
#  License: See LICENSE.txt
#
import os

from beets import plugins
from beets.dbcore import types
from beets.plugins import BeetsPlugin
from beets.util.confit import ConfigSource, load_yaml

from beetsplug.goingrunning import common as GRC
from beetsplug.goingrunning.command import GoingRunningCommand


class GoingRunningPlugin(BeetsPlugin):
    _default_plugin_config_file_name_ = 'config_default.yml'

    def __init__(self):
        super(GoingRunningPlugin, self).__init__()
        config_file_path = os.path.join(os.path.dirname(__file__), self._default_plugin_config_file_name_)
        source = ConfigSource(load_yaml(config_file_path) or {}, config_file_path)
        self.config.add(source)

    def commands(self):
        return [GoingRunningCommand(self.config)]

    @property
    def item_types(self):
        """Declare Float types for numeric flex attributes so that query parser will correctly use NumericQuery
        fixme: This creates conflict with the acousticbrainz plugin because of a bug in beets/plugins.py:340
        read here: test/functional/000_basic_test.py:38
        NOTE: It will allow declaring item_types if `acousticbrainz` plugin is not activated
        """
        item_types = {}

        conflicting_plugins = ['acousticbrainz']
        active_plugins = [plugin.name for plugin in plugins.find_plugins()]

        if not set(conflicting_plugins) <= set(active_plugins):
            # Conflicting plugins are not active
            for attr in GRC.KNOWN_NUMERIC_FLEX_ATTRIBUTES:
                item_types[attr] = types.Float(6)

        return item_types
