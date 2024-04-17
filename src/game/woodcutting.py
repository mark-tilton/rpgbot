from enum import Enum
import random
from typing import Mapping
from storage.activity import ActivityReward
from storage.item import Item

class Log(Enum):
    TEAK_LOG = Item.TEAK_LOG
    WALNUT_LOG = Item.WALNUT_LOG
    PINE_LOG = Item.PINE_LOG
    BIRCH_LOG = Item.BIRCH_LOG
    OAK_LOG = Item.OAK_LOG
    MAPLE_LOG = Item.MAPLE_LOG
    MAHOGANY_LOG = Item.MAHOGANY_LOG


def process_woodcutting(ticks: int) -> ActivityReward:
    items: Mapping[Item, int] = {}
    for _ in range(ticks):
        if random.random() * 100 < 30:
            if Item.BIRCH_LOG not in items:
                items[Item.BIRCH_LOG] = 0
            items[Item.BIRCH_LOG] += 1
    return ActivityReward(items)