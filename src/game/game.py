
from typing import Mapping, Optional
from game.activities import process_mining
from game.woodcutting import process_woodcutting, validate_woodcutting_activity
from game.validation import ValidationResult
from storage.equipment import EQUIPMENT_SLOT, Equipment
from storage.activity import Activity, ActivityReward, ActivityType
from storage.item import Item
from storage.storagemodel import StorageModel


class Game:
    def __init__(self):
        self.storage_model = StorageModel()

    def start_woodcutting(self, user_id: int, log_type: Item) -> ValidationResult:
        equipment = self.storage_model.get_player_equipment(user_id)
        result = validate_woodcutting_activity(equipment, log_type)
        if not result.valid:
            return result
        with self.storage_model as t:
            activity = self.start_activity(user_id=user_id, activity_type=ActivityType.WOODCUTTING)
            t.start_woodcutting(activity_id=activity.activity_id, log_type=log_type)
        return ValidationResult(True)

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
                for item, quantity in reward.items.items():
                    t.add_item(user_id, item, quantity)

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
    
    def get_player_items(self, user_id: int) -> Mapping[Item, int]:
        return self.storage_model.get_player_items(user_id=user_id)

    def buy_item(self, user_id, item: Item, quantity: int):
        with self.storage_model as t:
            t.add_item(user_id, item, quantity)
    
    def equip_item(self, user_id: int, item: Item) -> ValidationResult:
        if item not in EQUIPMENT_SLOT:
            return ValidationResult(False, "Item is not equippable")
        equipment_slot = EQUIPMENT_SLOT[item]
        current_equipment = self.storage_model.get_player_equipment(user_id)
        currently_equipped = current_equipment.get_slot(equipment_slot)

        with self.storage_model as t:
            if currently_equipped is not None:
                t.add_item(user_id, currently_equipped, 1)
            if not t.remove_item(user_id, item, 1):
                t.cancel()
                return ValidationResult(False, "Item not found in inventory")
            current_equipment.set_slot(equipment_slot, item)
            t.set_equipment(user_id, current_equipment)

        return ValidationResult(True)