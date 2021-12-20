#   Copyright: Copyright (c) 2020., Adam Jakab
#   Author: Adam Jakab <adam at jakab dot pro>
#   License: See LICENSE.txt
import hashlib
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from alive_progress import alive_bar
from beets import util
from confuse import Subview
from beetsplug.goingrunning import common


def generate_output(training: Subview, items, dry_run=False):
    exporter = ItemExport(training, items, dry_run)
    exporter.export()


class ItemExport:
    cfg_dry_run = False
    training: Subview = None
    items = []

    def __init__(self, training, items, dry_run=False):
        self.training = training
        self.items = items
        self.cfg_dry_run = dry_run

    def export(self):
        self._clean_target()
        self._copy_items()
        self._generate_playist()

    def _generate_playist(self):
        training_name = self._get_cleaned_training_name()
        playlist_name = self._get_training_name()
        target_name = common.get_training_attribute(self.training, "target")

        if not common.get_target_attribute_for_training(self.training,
                                                        "generate_playlist"):
            common.say("Playlist generation to target[{0}] was skipped "
                       "(generate_playlist=no).".
                       format(target_name), log_only=False)
            return

        dst_path = Path(common.get_destination_path_for_training(self.training))
        dst_sub_dir = dst_path.joinpath(training_name)
        playlist_filename = "{}.m3u".format(playlist_name)
        dst = dst_sub_dir.joinpath(playlist_filename)

        lines = [
            "# Playlist generated for training '{}' on {}". \
                format(training_name, datetime.now())
        ]

        for item in self.items:
            path = util.displayable_path(item.get("exportpath",
                                                  item.get("path")))
            if path:
                path = util.syspath(path)
                line = "{path}".format(path=path)
                lines.append(line)

        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as ntf:
            tmp_playlist = ntf.name
            for line in lines:
                ntf.write("{}\n".format(line).encode("utf-8"))

        common.say("Created playlist: {0}".format(dst), log_only=True)
        util.copy(tmp_playlist, dst)
        util.remove(tmp_playlist)

    def _copy_items(self):
        training_name = self._get_cleaned_training_name()
        target_name = common.get_training_attribute(self.training, "target")

        # The copy_files is only False when it is explicitly declared so
        copy_files = common.get_target_attribute_for_training(
            self.training, "copy_files")
        copy_files = False if copy_files == False else True

        if not copy_files:
            common.say("Copying to target[{0}] was skipped (copy_files=no).".
                       format(target_name))
            return

        increment_play_count = common.get_training_attribute(
            self.training, "increment_play_count")
        dst_path = Path(common.get_destination_path_for_training(self.training))

        dst_sub_dir = dst_path.joinpath(training_name)
        if not os.path.isdir(dst_sub_dir):
            os.mkdir(dst_sub_dir)

        common.say("Copying to target[{0}]: {1}".
                   format(target_name, dst_sub_dir))

        cnt = 0
        # todo: disable alive bar when running in verbose mode
        # from beets import logging as beetslogging
        # beets_log = beetslogging.getLogger("beets")
        # print(beets_log.getEffectiveLevel())

        with alive_bar(len(self.items)) as bar:
            for item in self.items:
                src = util.displayable_path(item.get("path"))
                if not os.path.isfile(src):
                    # todo: this is bad enough to interrupt! create option
                    # for this
                    common.say("File does not exist: {}".format(src))
                    continue

                fn, ext = os.path.splitext(src)
                gen_filename = "{0}_{1}{2}" \
                    .format(str(cnt).zfill(6), common.get_random_string(), ext)

                dst = dst_sub_dir.joinpath(gen_filename)
                # dst = "{0}/{1}".format(dst_path, gen_filename)

                common.say("Copying[{1}]: {0}".format(src, gen_filename))

                if not self.cfg_dry_run:
                    util.copy(src, dst)

                    # store the file_name for the playlist
                    item["exportpath"] = util.bytestring_path(gen_filename)

                    if increment_play_count:
                        common.increment_play_count_on_item(item)

                cnt += 1
                bar()

    def _clean_target(self):
        training_name = self._get_cleaned_training_name()
        target_name = common.get_training_attribute(self.training, "target")
        clean_target = common.get_target_attribute_for_training(
            self.training, "clean_target")

        if clean_target is False:
            return

        dst_path = Path(common.get_destination_path_for_training(self.training))

        # Clean entire target
        dst_sub_dir = dst_path

        # Only clean specific training folder
        if clean_target == "training":
            dst_sub_dir = dst_path.joinpath(training_name)

        common.say("Cleaning target[{0}]: {1}".
                   format(target_name, dst_sub_dir))

        if os.path.isdir(dst_sub_dir):
            shutil.rmtree(dst_sub_dir)
            os.mkdir(dst_sub_dir)

        # Clean additional files
        additional_files = common.get_target_attribute_for_training(
            self.training,
            "delete_from_device")
        if additional_files and len(additional_files) > 0:
            root = common.get_target_attribute_for_training(self.training,
                                                            "device_root")
            root = Path(root).expanduser()

            common.say("Deleting additional files: {0}".
                       format(additional_files))

            for path in additional_files:
                path = Path(str.strip(path, "/"))
                dst_path = os.path.realpath(root.joinpath(path))

                if not os.path.isfile(dst_path):
                    common.say(
                        "The file to delete does not exist: {0}".format(path),
                        log_only=True)
                    continue

                common.say("Deleting: {}".format(dst_path))
                if not self.cfg_dry_run:
                    os.remove(dst_path)

    def _get_training_name(self):
        # This will be the name of the playlist file
        training_name = str(self.training.name).split(".").pop()
        return training_name

    def _get_cleaned_training_name(self):
        # Some MPDs do not work well with folder names longer than 8 chars
        training_name = self._get_training_name()
        hash8 = hashlib.sha1(training_name.encode("UTF-8")) \
                    .hexdigest().upper()[:8]
        return hash8
