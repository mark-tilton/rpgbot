import random
from typing import Mapping, Optional
from game.woodcutting import process_woodcutting
from storage.item import Item
from storage.activity import ActivityReward, ActivityType, Activity

def process_activity(activity: Activity, elapsed_time: int) -> Optional[ActivityReward]:
    reward = None
    if activity.activity_type == ActivityType.COMBAT:
        ...
    elif activity.activity_type == ActivityType.WOODCUTTING:
        reward = process_woodcutting(elapsed_time)
    elif activity.activity_type == ActivityType.MINING:
        reward = process_mining(elapsed_time)
    return reward

def process_mining(ticks: int) -> ActivityReward:
    items: Mapping[Item, int] = {}
    for _ in range(ticks):
        if random.random() * 100 < 30:
            if Item.TIN_ORE not in items:
                items[Item.TIN_ORE] = 0
            items[Item.TIN_ORE] += random.randrange(1, 4)
    return ActivityReward(items)