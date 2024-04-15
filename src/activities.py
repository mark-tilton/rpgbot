import time
import random
from typing import Optional
from items import Item
from skills import get_level
from storagemodel import StorageModel
from datatypes import ActivityReward, ActivityType, Skills

def update_activity(model: StorageModel, user_id: int) -> Optional[ActivityReward]:
    current_tick = int(time.time())
    activity = model.get_current_activity(user_id)
    if activity is None:
        return None

    elapsed = current_tick - activity.start_tick
    reward = None
    if activity.activity_type == ActivityType.COMBAT:
        ...
    elif activity.activity_type == ActivityType.WOODCUTTING:
        reward = process_woodcutting(elapsed, 50000)
    elif activity.activity_type == ActivityType.MINING:
        reward = process_mining(elapsed, 50000)
    if reward is not None:
        model.apply_reward(user_id, reward)

    activity.start_tick = current_tick
    model.start_activity(user_id, activity)
    return reward

def process_woodcutting(ticks: int, woodcutting_xp: int) -> ActivityReward:
    experience = Skills(0, 0, 0)
    items = {}
    for _ in range(ticks):
        current_level = get_level(woodcutting_xp + experience.woodcutting_xp)
        if random.random() * 100 < current_level:
            experience.woodcutting_xp += 10
            items[Item.BIRCH_LOG] += 1
    return ActivityReward(experience, items)

def process_mining(ticks: int, mining_xp: int) -> ActivityReward:
    experience = Skills(0, 0, 0)
    items = {}
    for _ in range(ticks):
        current_level = get_level(mining_xp + experience.mining_xp)
        if random.random() * 100 < current_level:
            experience.mining_xp += 10
            if Item.TIN_ORE not in items:
                items[Item.TIN_ORE] = 0
            items[Item.TIN_ORE] += random.randrange(1, 4)
    return ActivityReward(experience, items)