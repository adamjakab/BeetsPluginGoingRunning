#  Copyright: Copyright (c) 2020., Adam Jakab
#  Author: Adam Jakab <adam at jakab dot pro>
#  License: See LICENSE.txt

import os

from beets import mediafile
from beets.dbcore import types
from beets.plugins import BeetsPlugin
from beets.util.confit import ConfigSource, load_yaml
from beetsplug.goingrunning.command import GoingRunningCommand


class GoingRunningPlugin(BeetsPlugin):
    _default_plugin_config_file_name_ = 'config_default.yml'

    def __init__(self):
        super(GoingRunningPlugin, self).__init__()

        # Read default configuration
        config_file_path = os.path.join(os.path.dirname(__file__),
                                        self._default_plugin_config_file_name_)
        source = ConfigSource(load_yaml(config_file_path) or {},
                              config_file_path)
        self.config.add(source)

        # Add `play_count` field support
        fld_name = u'play_count'
        if fld_name not in mediafile.MediaFile.fields():
            field = mediafile.MediaField(
                mediafile.MP3DescStorageStyle(fld_name),
                mediafile.StorageStyle(fld_name),
                out_type=int
            )
            self.add_media_field(fld_name, field)

    def commands(self):
        return [GoingRunningCommand(self.config)]

    @property
    def item_types(self):
        return {'play_count': types.INTEGER}
