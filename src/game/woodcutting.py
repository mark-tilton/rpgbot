import random
from typing import Mapping
from storage.activity import ActivityReward
from storage.item import Item

LOG_TYPES = [
    Item.TEAK_LOG,
    Item.WALNUT_LOG,
    Item.PINE_LOG,
    Item.BIRCH_LOG,
    Item.OAK_LOG,
    Item.MAPLE_LOG,
    Item.MAHOGANY_LOG,
]


def process_woodcutting(ticks: int, log_type: Item) -> ActivityReward:
    items: Mapping[Item, int] = {}
    for _ in range(ticks):
        if random.random() * 100 < 30:
            if log_type not in items:
                items[log_type] = 0
            items[log_type] += 1
    return ActivityReward(items)