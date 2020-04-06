#   Copyright: Copyright (c) 2020., Adam Jakab
#   Author: Adam Jakab <adam at jakab dot pro>
#   License: See LICENSE.txt
import operator
from abc import ABC
from abc import abstractmethod
from random import uniform

from beets.util.confit import Subview
from beetsplug.goingrunning import common

permutations = {
    'unordered': {
        'module': 'beetsplug.goingrunning.itemorder',
        'class': 'UnorderedPermutation'
    },
    'score_based_linear': {
        'module': 'beetsplug.goingrunning.itemorder',
        'class': 'ScoreBasedLinearPermutation'
    }
}

default_strategy = 'unordered'


def get_ordered_items(training: Subview, items):
    """Returns the items ordered by the strategy specified in the
    `ordering_strategy` key
    """
    strategy = common.get_training_attribute(training, "ordering_strategy")
    if not strategy or strategy not in permutations:
        strategy = default_strategy

    perm = permutations[strategy]
    instance: BasePermutation = common.get_class_instance(
        perm["module"], perm["class"])
    instance.setup(training, items)
    return instance.get_ordered_items()


def _get_field_info_value(field_info, strategy="zero"):
    answer = field_info["min"]
    if strategy == "average":
        answer = round(field_info["delta"] / 2, 6)
    elif strategy == "random":
        answer = round(uniform(field_info["min"], field_info["max"]), 6)

    return answer


class BasePermutation(ABC):
    training: Subview = None
    items = []

    def __init__(self):
        common.say("ORDERING permutation: {0}".format(self.__class__.__name__))

    def setup(self, training: Subview, items):
        self.training = training
        self.items = items

    @abstractmethod
    def get_ordered_items(self):
        raise NotImplementedError("You must implement this method.")


class UnorderedPermutation(BasePermutation):
    def __init__(self):
        super(UnorderedPermutation, self).__init__()

    def get_ordered_items(self):
        return self.items


class ScoreBasedLinearPermutation(BasePermutation):
    no_value_strategy = "zero"  # (zero|average|random)
    order_info = None

    def __init__(self):
        super(ScoreBasedLinearPermutation, self).__init__()

    def setup(self, training: Subview, items):
        super().setup(training, items)
        self._build_order_info()
        self._score_items()

    def get_ordered_items(self):
        sorted_items = sorted(self.items,
                              key=operator.attrgetter('ordering_score'))

        return sorted_items

    def _score_items(self):

        # Score the library items
        for item in self.items:
            item["ordering_score"] = 0
            item["ordering_info"] = {}
            for field_name in self.order_info.keys():
                field_info = self.order_info[field_name]

                try:
                    field_value = round(float(item.get(field_name, None)), 3)
                except ValueError:
                    field_value = None
                except TypeError:
                    field_value = None

                if field_value is None:
                    field_value = _get_field_info_value(field_info,
                                                        self.no_value_strategy)

                distance_from_min = round(field_value - field_info["min"], 6)

                # Linear - field_score should always be between 0 and 100
                field_score = round(distance_from_min * field_info["step"], 6)
                field_score = field_score if field_score > 0 else 0
                field_score = field_score if field_score < 100 else 100

                weighted_field_score = round(
                    field_info["weight"] * field_score / 100, 6)

                item["ordering_score"] = round(
                    item["ordering_score"] + weighted_field_score, 6)

                item["ordering_info"][field_name] = {
                    "distance_from_min": distance_from_min,
                    "field_score": field_score,
                    "weighted_field_score": weighted_field_score
                }

            # common.say("score:{} - info:{}".format(
            #     item["ordering_score"],
            #     item["ordering_info"]
            # ))

    def _build_order_info(self):
        cfg_ordering = {}
        fields = []

        common.say("Scoring {} items...".format(len(self.items)))

        if self.training["ordering"].exists() and \
                len(self.training["ordering"].keys()) > 0:
            cfg_ordering = self.training["ordering"].get()
            fields = list(cfg_ordering.keys())

        default_field_data = {
            "min": 99999999.9,
            "max": 0.0,
            "delta": 0.0,
            "step": 0.0,
            "weight": 100
        }

        # Build Order Info dictionary
        self.order_info = {}
        for field in fields:
            field_name = field.strip()
            self.order_info[field_name] = default_field_data.copy()
            self.order_info[field_name]["weight"] = cfg_ordering[field]

        # Populate Order Info
        for field_name in self.order_info.keys():
            field_info = self.order_info[field_name]
            _min, _max, _sum, _avg = common.get_min_max_sum_avg_for_items(
                self.items, field_name)
            field_info["min"] = _min
            field_info["max"] = _max

        # Calculate other values in Order Info
        for field_name in self.order_info.keys():
            field_info = self.order_info[field_name]
            field_info["delta"] = round(field_info["max"] - field_info[
                "min"], 6)
            if field_info["delta"] > 0:
                field_info["step"] = round(100 / field_info["delta"], 6)
            else:
                field_info["step"] = 0

        common.say("ORDER INFO: {0}".format(self.order_info))
