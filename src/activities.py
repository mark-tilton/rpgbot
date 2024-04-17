import time
import random
from typing import Optional
from items import Item
from skills import get_level
from storagemodel import StorageModel
from datatypes import ActivityReward, ActivityType, Skills, Activity

def process_activity(activity: Activity, elapsed_time: int) -> Optional[ActivityReward]:
    reward = None
    if activity.activity_type == ActivityType.COMBAT:
        ...
    elif activity.activity_type == ActivityType.WOODCUTTING:
        reward = process_woodcutting(elapsed_time, 50000)
    elif activity.activity_type == ActivityType.MINING:
        reward = process_mining(elapsed_time, 50000)
    return reward

def start_activity(model: StorageModel, user_id: int, activity_type: ActivityType) -> Optional[Activity]:
    current_tick = int(time.time())
    update_activity(model=model, user_id=user_id, current_tick=current_tick)
    model.start_activity(user_id=user_id, activity_type=activity_type, start_tick=current_tick)

def update_activity(model: StorageModel, user_id: int, current_tick: Optional[int] = None):
    if not current_tick:
        current_tick = int(time.time())
    activity = model.get_current_activity(user_id)
    if activity is None:
        return None

    elapsed = current_tick - activity.last_updated
    reward = process_activity(activity=activity, elapsed_time=elapsed)

    model.update_activity(activity=activity, reward=reward, current_tick=current_tick)

def process_woodcutting(ticks: int, woodcutting_xp: int) -> ActivityReward:
    experience = Skills()
    items = {}
    for _ in range(ticks):
        current_level = get_level(woodcutting_xp + experience.woodcutting_xp)
        if random.random() * 100 < current_level:
            experience.woodcutting_xp += 10
            if Item.BIRCH_LOG not in items:
                items[Item.BIRCH_LOG] = 0
            items[Item.BIRCH_LOG] += 1
    return ActivityReward(experience, items)

def process_mining(ticks: int, mining_xp: int) -> ActivityReward:
    experience = Skills()
    items = {}
    for _ in range(ticks):
        current_level = get_level(mining_xp + experience.mining_xp)
        if random.random() * 100 < current_level:
            experience.mining_xp += 10
            if Item.TIN_ORE not in items:
                items[Item.TIN_ORE] = 0
            items[Item.TIN_ORE] += random.randrange(1, 4)
    return ActivityReward(experience, items)