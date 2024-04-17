
import time
from typing import Mapping, Optional
from game.activities import process_activity
from datatypes import Activity, ActivityType
from items import Item
from storagemodel import StorageModel


class Game:
    def __init__(self):
        self.storage_model = StorageModel()

    def start_activity(self, user_id: int, activity_type: ActivityType) -> Optional[Activity]:
        current_tick = int(time.time())
        self.update_activity(user_id=user_id, current_tick=current_tick)
        self.storage_model.start_activity(user_id=user_id, activity_type=activity_type, start_tick=current_tick)

    def update_activity(self, user_id: int, current_tick: Optional[int] = None):
        if not current_tick:
            current_tick = int(time.time())
        activity = self.storage_model.get_current_activity(user_id)
        if activity is None:
            return None

        elapsed = current_tick - activity.last_updated
        reward = process_activity(activity=activity, elapsed_time=elapsed)

        self.storage_model.update_activity(activity=activity, reward=reward, current_tick=current_tick)
    
    def get_player_items(self, user_id: int) -> Mapping[Item, int]:
        return self.storage_model.get_player_items(user_id=user_id)