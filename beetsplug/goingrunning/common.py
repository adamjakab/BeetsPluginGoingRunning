#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 12:29 PM
#  License: See LICENSE.txt
#

import logging
import sys

from beets.dbcore import types
from beets.library import Item
from beets.util.confit import Subview

MUST_HAVE_TRAINING_KEYS = ['duration', 'query', 'target']
MUST_HAVE_TARGET_KEYS = ['device_root', 'device_path']

KNOWN_NUMERIC_FLEX_ATTRIBUTES = [
    "average_loudness",
    "chords_changes_rate",
    "chords_number_rate",
    "danceable",
    "key_strength"
    "mood_acoustic",
    "mood_aggressive",
    "mood_electronic",
    "mood_happy",
    "mood_party",
    "mood_relaxed",
    "mood_sad",
    "rhythm"
    "tonal",
]

KNOWN_TEXTUAL_FLEX_ATTRIBUTES = [
    "gender",
    "genre_rosamerica",
    "rhythm",
    "voice_instrumental",
    "chords_key",
    "chords_scale"
]

__logger__ = logging.getLogger('beets.goingrunning')


def say(msg, log_only=False):
    """Log and write to stdout
    """
    __logger__.debug(msg)
    if not log_only:
        sys.stdout.write(msg + "\n")


def get_item_attribute_type_overrides():
    _types = {}
    for attr in KNOWN_NUMERIC_FLEX_ATTRIBUTES:
        _types[attr] = types.Float(6)

    return _types


def get_human_readable_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


def get_beet_query_formatted_string(key, val):
    quote_val = type(val) == str and " " in val
    fmt = "{k}:'{v}'" if quote_val else "{k}:{v}"
    return fmt.format(k=key, v=val)

def get_flavour_elements(flavour: Subview):
    elements = []

    if not flavour.exists():
        return elements

    for key in flavour.keys():
        # todo: in future flavours can have "use_flavours" key to make this recursive
        elements.append(get_beet_query_formatted_string(key, flavour[key].get()))

    return elements

def get_training_attribute(training: Subview, attrib: str):
    """Returns the attribute value from "goingrunning.trainings" for the specified training or uses the
    spacial fallback training configuration.
    """
    value = None
    if training[attrib].exists():
        value = training[attrib].get()
    elif training.name != "goingrunning.trainings.fallback" and training.parent["fallback"].exists():
        fallback = training.parent["fallback"]
        value = get_training_attribute(fallback, attrib)

    return value

def get_target_attribute(target: Subview, attrib: str):
    """Returns the attribute value from "goingrunning.targets" for the specified target.
    """
    value = None
    if target[attrib].exists():
        value = target[attrib].get()

    return value

def get_duration_of_items(items):
    """
    Calculate the total duration of the media items using the "length" attribute
    :param items: list
    :return: int
    """
    total_time = 0

    if isinstance(items, list):
        for item in items:
            try:
                total_time += int(item.get("length"))
            except TypeError:
                pass
            except ValueError:
                pass

    return total_time


def get_min_max_sum_avg_for_items(items, field_name):
    _min = 99999999.9
    _max = 0
    _sum = 0
    _avg = 0
    _cnt = 0
    for item in items:
        try:
            field_value = round(float(item.get(field_name, None)), 3)
            _cnt += 1
        except ValueError:
            field_value = None
        except TypeError:
            field_value = None

        # Min
        if field_value is not None and field_value < _min:
            _min = field_value

        # Max
        if field_value is not None and field_value > _max:
            _max = field_value

        # Sum
        if field_value is not None:
            _sum = _sum + field_value

    # Avg
    if _cnt > 0:
        _avg = round(_sum / _cnt, 3)

    return _min, _max, _sum, _avg


def score_library_items(training: Subview, items):
    ordering = {}
    fields = []
    if training["ordering"].exists() and len(training["ordering"].keys()) > 0:
        ordering = training["ordering"].get()
        fields = list(ordering.keys())

    default_field_data = {
        "min": 99999999.9,
        "max": 0.0,
        "delta": 0.0,
        "step": 0.0,
        "weight": 100
    }

    # Build Order Info
    order_info = {}
    for field in fields:
        field_name = field.strip()
        order_info[field_name] = default_field_data.copy()
        order_info[field_name]["weight"] = ordering[field]

    # self._say("ORDER INFO #1: {0}".format(order_info))

    # Populate Order Info
    for field_name in order_info.keys():
        field_data = order_info[field_name]
        _min, _max, _sum, _avg = get_min_max_sum_avg_for_items(items, field_name)
        field_data["min"] = _min
        field_data["max"] = _max

    # self._say("ORDER INFO #2: {0}".format(order_info))

    # todo: this will not work anymore - find a better way
    # Remove bad items from Order Info
    # bad_oi = [field for field in order_info if
    #           order_info[field]["min"] == default_field_data["min"] and
    #           order_info[field]["max"] == default_field_data["max"]
    #           ]
    # for field in bad_oi: del order_info[field]
    # self._say("ORDER INFO #3: {0}".format(order_info))

    # Calculate other values in Order Info
    for field_name in order_info.keys():
        field_data = order_info[field_name]
        field_data["delta"] = field_data["max"] - field_data["min"]
        if field_data["delta"] > 0:
            field_data["step"] = round(100 / field_data["delta"], 3)
        else:
            field_data["step"] = 0

    # self._say("ORDER INFO: {0}".format(order_info))

    # Score the library items
    for item in items:
        item: Item
        item["ordering_score"] = 0
        item["ordering_info"] = {}
        for field_name in order_info.keys():
            field_data = order_info[field_name]
            try:
                field_value = round(float(item.get(field_name, None)), 3)
            except ValueError:
                field_value = None
            except TypeError:
                field_value = None

            if field_value is None:
                # Make up average value
                field_value = round(field_data["delta"] / 2, 3)

            distance_from_min = round(field_value - field_data["min"], 3)

            # This is linear (we could some day use different models)
            # field_score should always be between 0 and 100
            field_score = round(distance_from_min * field_data["step"], 3)
            field_score = field_score if field_score > 0 else 0
            field_score = field_score if field_score < 100 else 100

            weighted_field_score = round(
                field_data["weight"] * field_score / 100, 3)

            item["ordering_score"] = round(
                item["ordering_score"] + weighted_field_score, 3)

            item["ordering_info"][field_name] = {
                "distance_from_min": distance_from_min,
                "field_score": field_score,
                "weighted_field_score": weighted_field_score
            }
