
from typing import Mapping, Optional
from game.activities import process_mining
from game.woodcutting import process_woodcutting
from storage.activity import Activity, ActivityReward, ActivityType
from storage.item import Item
from storage.storagemodel import StorageModel


class Game:
    def __init__(self):
        self.storage_model = StorageModel()

    def start_woodcutting(self, user_id: int, log_type: Item):
        with self.storage_model as t:
            activity = self.start_activity(user_id=user_id, activity_type=ActivityType.WOODCUTTING)
            t.start_woodcutting(activity_id=activity.activity_id, log_type=log_type)

    def start_activity(self, user_id: int, activity_type: ActivityType) -> Activity:
        with self.storage_model as t:
            self.update_activity(user_id=user_id)
            return t.start_activity(user_id=user_id, activity_type=activity_type)

    def update_activity(self, user_id: int):
        activity = self.storage_model.get_current_activity(user_id)
        if activity is None:
            return None

        with self.storage_model as t:
            elapsed = t.current_tick - activity.last_updated
            reward = self.process_activity(activity=activity, elapsed_time=elapsed)

            t.update_activity(activity=activity)
            if reward:
                t.apply_reward(activity=activity, reward=reward)
    
    def get_player_items(self, user_id: int) -> Mapping[Item, int]:
        return self.storage_model.get_player_items(user_id=user_id)

    def process_activity(self, activity: Activity, elapsed_time: int) -> Optional[ActivityReward]:
        reward = None
        if activity.activity_type == ActivityType.COMBAT:
            ...
        elif activity.activity_type == ActivityType.WOODCUTTING:
            log_type = self.storage_model.get_woodcutting_info(activity.activity_id)
            if not log_type:
                raise Exception("Log type not found for woodcutting activity.")
            reward = process_woodcutting(elapsed_time, log_type)
        elif activity.activity_type == ActivityType.MINING:
            reward = process_mining(elapsed_time)
        return reward