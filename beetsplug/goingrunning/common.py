#  Copyright: Copyright (c) 2020., Adam Jakab
#  Author: Adam Jakab <adam at jakab dot pro>
#  License: See LICENSE.txt
import importlib
import logging
import os

from beets.dbcore import types
from beets.library import Item
from beets.util.confit import Subview

# Get values as: plg_ns['__PLUGIN_NAME__']
plg_ns = {}
about_path = os.path.join(os.path.dirname(__file__), u'about.py')
with open(about_path) as about_file:
    exec(about_file.read(), plg_ns)

MUST_HAVE_TRAINING_KEYS = ['duration', 'query', 'target']
MUST_HAVE_TARGET_KEYS = ['device_root', 'device_path']

KNOWN_NUMERIC_FLEX_ATTRIBUTES = [
    "average_loudness",
    "chords_changes_rate",
    "chords_number_rate",
    "danceable",
    "key_strength",
    "mood_acoustic",
    "mood_aggressive",
    "mood_electronic",
    "mood_happy",
    "mood_party",
    "mood_relaxed",
    "mood_sad",
    "rhythm",
    "tonal",
]

KNOWN_TEXTUAL_FLEX_ATTRIBUTES = [
    "gender",
    "genre_rosamerica",
    "rhythm",
    "voice_instrumental",
    "chords_key",
    "chords_scale",
]

__logger__ = logging.getLogger('beets.{plg}'.format(plg=plg_ns[
    '__PLUGIN_NAME__']))


def say(msg, log_only=True, is_error=False):
    _level = logging.DEBUG
    _level = _level if log_only else logging.INFO
    _level = _level if not is_error else logging.ERROR
    __logger__.log(level=_level, msg=msg)


def get_item_attribute_type_overrides():
    _types = {}
    for attr in KNOWN_NUMERIC_FLEX_ATTRIBUTES:
        _types[attr] = types.Float(6)

    return _types


def get_human_readable_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


def get_query_element_string(key, val):
    return "{k}:{v}".format(k=key, v=val)

def get_flavour_elements(flavour: Subview):
    elements = []

    if not flavour.exists():
        return elements

    for key in flavour.keys():
        # todo: in future flavours can have "use_flavours" key to make this recursive
        elements.append(get_query_element_string(key, flavour[key].get()))

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
    """
    total_time = 0

    if isinstance(items, list):
        for item in items:
            try:
                total_time += item.get("length")
            except TypeError:
                pass
            except ValueError:
                pass

    return round(total_time)


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

    # Min (correction)
    if _min > _max:
        _min = _max

    # Avg
    if _cnt > 0:
        _avg = round(_sum / _cnt, 3)

    return _min, _max, _sum, _avg


def increment_play_count_on_item(item: Item):
    # clear_dirty is necessary to make sure that `ordering_score` and
    # `ordering_info` will not get stored to the library
    item.clear_dirty()
    item["play_count"] = item.get("play_count", 0) + 1
    item.store()
    item.write()


def get_class_instance(module_name, class_name):
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as err:
        raise RuntimeError("Module load error! {}".format(err))

    try:
        klass = getattr(module, class_name)
        instance = klass()
    except BaseException as err:
        raise RuntimeError("Instance creation error! {}".format(err))

    return instance
