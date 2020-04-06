#  Copyright: Copyright (c) 2020., Adam Jakab
#  Author: Adam Jakab <adam at jakab dot pro>
#  License: See LICENSE.txt
import importlib
# todo: use beets logger?!
# from beets import logging
import logging
import os
from pathlib import Path

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


def say(msg: str, log_only=True, is_error=False):
    """
    https://beets.readthedocs.io/en/stable/dev/plugins.html#logging
    """
    _level = logging.DEBUG
    _level = _level if log_only else logging.INFO
    _level = _level if not is_error else logging.ERROR
    msg = msg.replace('\'', '"')
    __logger__.log(level=_level, msg=msg)


def get_item_attribute_type_overrides():
    _types = {}
    for attr in KNOWN_NUMERIC_FLEX_ATTRIBUTES:
        _types[attr] = types.Float(6)

    return _types


def get_human_readable_time(seconds):
    """Formats seconds as a short human-readable HH:MM:SS string.
    """
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


def get_normalized_query_element(key, val):
    answer = ""

    tpl = "{k}:{v}"
    if type(val) in [str, int, float, bool]:
        answer = tpl.format(k=key, v=val)
    elif type(val) == list:
        answer = []
        for v in val:
            answer.append(tpl.format(k=key, v=v))

    return answer


def get_flavour_elements(flavour: Subview):
    elements = []

    if not flavour.exists():
        return elements

    for key in flavour.keys():
        # todo: in future flavours can have "use_flavours" key to make this
        #  recursive
        nqe = get_normalized_query_element(key, flavour[key].get())
        if type(nqe) == list:
            elements.extend(nqe)
        else:
            elements.append(nqe)

    return elements


def get_training_attribute(training: Subview, attrib: str):
    """Returns the attribute value from "goingrunning.trainings" for the
    specified training or uses the
    spacial fallback training configuration.
    """
    value = None
    if training[attrib].exists():
        value = training[attrib].get()
    elif training.name != "goingrunning.trainings.fallback" and training.parent[
        "fallback"].exists():
        fallback = training.parent["fallback"]
        value = get_training_attribute(fallback, attrib)

    return value


def get_target_for_training(training: Subview):
    answer = None

    target_name = get_training_attribute(training, "target")
    say("Finding target: {0}".format(target_name))

    cfg_targets: Subview = training.parent.parent["targets"]
    if not cfg_targets.exists():
        say("Cannot find 'targets' node!")
    elif not cfg_targets[target_name].exists():
        say("Target name '{0}' is not defined!".format(target_name))
    else:
        answer = cfg_targets[target_name]

    return answer


def get_target_attribute_for_training(training: Subview,
                                      attrib: str = "name"):
    answer = None

    target_name = get_training_attribute(training, "target")
    say("Getting attribute[{0}] for target: {1}".format(attrib, target_name),
        log_only=True)

    target = get_target_for_training(training)
    if target:
        if attrib == "name":
            answer = target_name
        else:
            answer = get_target_attribute(target, attrib)

        say("Found target[{0}] attribute[{1}] path: {2}".
            format(target_name, attrib, answer), log_only=True)

    return answer


def get_destination_path_for_training(training: Subview):
    answer = None

    target_name = get_training_attribute(training, "target")

    if not target_name:
        say("Training does not declare a `target`!".
            format(target_name), log_only=False)
        return answer

    root = get_target_attribute_for_training(training, "device_root")
    path = get_target_attribute_for_training(training, "device_path")
    path = path or ""

    if not root:
        say("The target[{0}] does not declare a device root path.".
            format(target_name), log_only=False)
        return answer

    root = Path(root).expanduser()
    path = Path(str.strip(path, "/"))
    dst_path = os.path.realpath(root.joinpath(path))

    if not os.path.isdir(dst_path):
        say("The target[{0}] path does not exist: {1}".
            format(target_name, dst_path), log_only=False)
        return answer

    say("Found target[{0}] path: {0}".
        format(target_name, dst_path), log_only=True)

    return dst_path


def get_target_attribute(target: Subview, attrib: str):
    """Returns the attribute value from "goingrunning.targets" for the
    specified target.
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
                length = item.get("length")
                if not length or length <= 0:
                    raise ValueError("Invalid length value!")
                total_time += length
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


def increment_play_count_on_item(item: Item, store=True, write=True):
    # clear_dirty is necessary to make sure that `ordering_score` and
    # `ordering_info` will not get stored to the library
    item.clear_dirty()
    item["play_count"] = item.get("play_count", 0) + 1
    if store:
        item.store()
    if write:
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
