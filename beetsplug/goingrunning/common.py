#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 12:29 PM
#  License: See LICENSE.txt
#

import logging
from beets.util.confit import Subview
from beets.random import random_objs

MUST_HAVE_TRAINING_KEYS = ['query', 'duration', 'target']
MUST_HAVE_TARGET_KEYS = ['device_root', 'device_path']

KNOWN_NUMERIC_FLEX_ATTRIBUTES = ["danceable", "mood_acoustic", "mood_aggressive", "mood_electronic", "mood_happy",
                                 "mood_party", "mood_relaxed", "mood_sad", "tonal", "average_loudness",
                                 "chords_changes_rate", "chords_number_rate", "key_strength"]

KNOWN_TEXTUAL_FLEX_ATTRIBUTES = ["gender", "genre_rosamerica", "rhythm", "voice_instrumental", "chords_key",
                                 "chords_scale"]


def get_beets_logger():
    return logging.getLogger('beets.goingrunning')

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
