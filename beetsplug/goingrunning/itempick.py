#   Copyright: Copyright (c) 2020., Adam Jakab
#   Author: Adam Jakab <adam at jakab dot pro>
#   License: See LICENSE.txt

from abc import ABC
from abc import abstractmethod
from random import randint

from beets.library import Item
from beets.util.confit import Subview
from beetsplug.goingrunning import common

pickers = {
    'top': {
        'module': 'beetsplug.goingrunning.itempick',
        'class': 'TopPicker'
    },
    'random_from_bins': {
        'module': 'beetsplug.goingrunning.itempick',
        'class': 'RandomFromBinsPicker'
    }
}

default_picker = 'top'
favour_unplayed = False


def get_items_for_duration(training: Subview, items, duration):
    """Returns the items picked by the Picker strategy specified bu the
        `pick_strategy` key
        """
    picker = common.get_training_attribute(training, "pick_strategy")
    if not picker or picker not in pickers:
        picker = default_picker

    picker_info = pickers[picker]
    instance: BasePicker = common.get_class_instance(
        picker_info["module"], picker_info["class"])
    instance.setup(training, items, duration)
    return instance.get_picked_items()


class BasePicker(ABC):
    training: Subview = None
    items = []
    duration = 0
    selection = []

    def __init__(self):
        common.say("PICKER strategy: {0} ('favour_unplayed': {1})".
                   format(self.__class__.__name__,
                          'yes' if favour_unplayed else 'no'
                          ))

    def setup(self, training: Subview, items, duration):
        self.training = training
        self.items = items
        self.duration = duration
        self.selection = []

    @abstractmethod
    def _make_selection(self):
        raise NotImplementedError("You must implement this method.")

    def get_picked_items(self):
        answer = []

        self._make_selection()

        for sel_data in self.selection:
            index = sel_data["index"]
            item = self.items[index]
            answer.append(item)

        return answer


class TopPicker(BasePicker):
    def __init__(self):
        super(TopPicker, self).__init__()

    def _make_selection(self):
        sel_dur = 0
        while sel_dur < self.duration and len(self.items) > 0:
            index = len(self.items) - 1
            item: Item = self.items[index]
            sel_data = {
                "index": index,
                "length": item.get("length")
            }
            sel_dur += round(item.get("length"))
            self.selection.append(sel_data)


class RandomFromBinsPicker(BasePicker):
    bin_boundaries = []
    max_allowed_time_difference = 120

    def __init__(self):
        super(RandomFromBinsPicker, self).__init__()

    def _make_selection(self):
        self._setup_bin_boundaries()
        self._make_initial_selection()
        self._improve_selection()

    def _improve_selection(self):
        # Try to get as close to duration as possible
        max_overtime = 10
        sel_time = sum(l["length"] for l in self.selection)
        curr_sel = 0
        curr_run = 0
        max_run = len(self.bin_boundaries) * 3
        exclusions = {}

        if not self.selection:
            common.say("IMPROVEMENTS: SKIPPED (No initial selection)")
            return

        # iterate through initial selection items and try to find a better
        # alternative for them
        while sel_time < self.duration or sel_time > self.duration + \
                max_overtime:
            curr_run += 1
            if curr_run > max_run:
                common.say("MAX HIT!")
                break
            # common.say("{} IMPROVEMENT RUN: {}/{}".
            #     format("=" * 60, curr_run, max_run))

            curr_bin = self.selection[curr_sel]["bin"]
            curr_index = self.selection[curr_sel]["index"]
            curr_len = self.selection[curr_sel]["length"]

            # if positive we need shorter songs if negative then longer
            time_diff = abs(round(sel_time - self.duration))
            min_len = curr_len - time_diff
            max_len = curr_len + time_diff

            if curr_bin not in exclusions.keys():
                exclusions[curr_bin] = [curr_index]
            exclude = exclusions[curr_bin]
            index = self._get_item_within_length(curr_bin, min_len, max_len,
                                                 exclude_indices=exclude)
            if index is not None:
                exclude.append(index)
                item: Item = self.items[index]
                item_len = item.get("length")
                new_diff = abs((sel_time - curr_len + item_len) - self.duration)

                if new_diff < time_diff:
                    sel_data = {
                        "index": index,
                        "bin": curr_bin,
                        "length": item_len,
                        "play_count": item.get("play_count", 0)
                    }
                    del self.selection[curr_sel]
                    self.selection.insert(curr_sel, sel_data)
                    sel_time = round(sum(l["length"] for l in self.selection))

                    common.say("{} IMPROVEMENT RUN: {}/{}".
                               format("=" * 60, curr_run, max_run))
                    common.say("PROPOSAL[bin: {}](index: {}): {} -> {}".
                               format(curr_bin, index,
                                      round(curr_len), round(item_len)))
                    common.say("IMPROVED BY: {} sec".
                               format(round(time_diff - new_diff)))
                    self.show_selection_status()

            if curr_sel < len(self.selection) - 1:
                curr_sel += 1
            else:
                curr_sel = 0

        common.say("{} IMPROVEMENTS: FINISHED".format("=" * 60))
        self.show_selection_status()
        common.say("SELECTION: {}".format(self.selection))

    def _make_initial_selection(self):
        # Create an initial selection
        sel_time = 0
        curr_bin = 0
        max_bin = len(self.bin_boundaries) - 1
        curr_run = 0
        max_run = 100
        while (self.duration - sel_time) > self.max_allowed_time_difference:
            curr_run += 1
            if curr_run > max_run:
                common.say("MAX HIT!")
                break
            low, high = self._get_bin_boundaries(curr_bin)
            if low is None or high is None:
                curr_bin = curr_bin + 1 if curr_bin < max_bin else 0
                continue
            index = self._get_random_item_between_boundaries(low, high)
            if index is not None:
                item: Item = self.items[index]
                item_len = item.get("length")
                time_diff = abs(sel_time - self.duration)
                new_diff = abs((sel_time + item_len) - self.duration)

                if new_diff < time_diff:
                    sel_data = {
                        "index": index,
                        "bin": curr_bin,
                        "length": item_len,
                        "play_count": item.get("play_count", 0)
                    }
                    self.selection.append(sel_data)
                    sel_time += item_len
                    curr_bin = curr_bin + 1 if curr_bin < max_bin else 0

        common.say("{} INITIAL SELECTION: FINISHED".format("=" * 60))
        self.show_selection_status()

    def _get_item_within_length(self, bin_number,
                                min_len, max_len, exclude_indices=None):
        index = None
        if exclude_indices is None:
            exclude_indices = []

        low, high = self._get_bin_boundaries(bin_number)
        if low is None or high is None:
            return index

        candidates = []
        for i in range(low, high):
            if i not in exclude_indices and \
                    min_len < self.items[i].get("length") < max_len:
                candidates.append(i)

        bin_items = self.items[low:high]
        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items(
            bin_items, "play_count")
        _min = int(_min)
        _max = int(_max) if _max > _min else _min + 1

        found = False
        for pc in range(_min, _max):
            attempts = round(len(candidates) / 2)
            while attempts > 0:
                attempts -= 1
                ci = randint(0, len(candidates) - 1)
                index = candidates[ci]
                if self.items[index].get("play_count", 0) == pc:
                    found = True
                    break
            if found:
                break

        return index

    def _get_bin_boundaries(self, bin_number):
        low = None
        high = None
        try:
            low, high = self.bin_boundaries[bin_number]
        except IndexError:
            pass

        return low, high

    def _setup_bin_boundaries(self):
        self.bin_boundaries = []

        if len(self.items) <= 1:
            raise ValueError("There is only one song in the selection!")

        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items(
            self.items, "length")

        if not _avg:
            raise ValueError("Average song length is zero!")

        num_bins = round(self.duration / _avg)
        bin_size = round(len(self.items) / num_bins)

        common.say("Number of bins: {}".format(num_bins))
        common.say("Bin size: {}".format(bin_size))

        if not bin_size or bin_size * num_bins > len(self.items):
            low = 0
            high = len(self.items) - 1
            self.bin_boundaries.append([low, high])
        else:
            for bi in range(0, num_bins):
                is_last_bin = bi == (num_bins - 1)
                low = bi * bin_size
                high = low + bin_size - 1
                if is_last_bin:
                    high = len(self.items) - 1
                self.bin_boundaries.append([low, high])

        common.say("Bin boundaries: {}".format(self.bin_boundaries))

    def _get_random_item_between_boundaries(self, low, high):
        if not favour_unplayed:
            return randint(low, high)

        bin_items = self.items[low:high]
        _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items(
            bin_items, "play_count")
        _min = int(_min)
        _max = int(_max) if _max > _min else _min + 1

        index = None
        found = False
        for pc in range(_min, _max):
            attempts = round(len(bin_items) / 2)
            while attempts > 0:
                attempts -= 1
                index = randint(low, high)
                if self.items[index].get("play_count", 0) == pc:
                    found = True
                    break
            if found:
                break

        return index

    def show_selection_status(self):
        sel_time = sum(l["length"] for l in self.selection)
        time_diff = sel_time - self.duration
        common.say("TOTAL(sec):{} SELECTED(sec):{} DIFFERENCE(sec):{}".format(
            self.duration, round(sel_time), round(time_diff)))
