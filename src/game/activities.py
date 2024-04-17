import random
from typing import Mapping, Optional
from storage.items import Item
from storage.datatypes import ActivityReward, ActivityType, Activity

def process_activity(activity: Activity, elapsed_time: int) -> Optional[ActivityReward]:
    reward = None
    if activity.activity_type == ActivityType.COMBAT:
        ...
    elif activity.activity_type == ActivityType.WOODCUTTING:
        reward = process_woodcutting(elapsed_time)
    elif activity.activity_type == ActivityType.MINING:
        reward = process_mining(elapsed_time)
    return reward

def process_woodcutting(ticks: int) -> ActivityReward:
    items: Mapping[Item, int] = {}
    for _ in range(ticks):
        if random.random() * 100 < 30:
            if Item.BIRCH_LOG not in items:
                items[Item.BIRCH_LOG] = 0
            items[Item.BIRCH_LOG] += 1
    return ActivityReward(items)

def process_mining(ticks: int) -> ActivityReward:
    items: Mapping[Item, int] = {}
    for _ in range(ticks):
        if random.random() * 100 < 30:
            if Item.TIN_ORE not in items:
                items[Item.TIN_ORE] = 0
            items[Item.TIN_ORE] += random.randrange(1, 4)
    return ActivityReward(items)