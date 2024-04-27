import time
from math import floor

from storage.storagemodel import StorageModel, TagType

from .adventure import Adventure, AdventureReport, process_adventure
from .tags import Inventory


class Game:
    def __init__(self):
        self.storage_model = StorageModel()

    def start_adventure(self, user_id: int, zone_id: str) -> AdventureReport | None:
        with self.storage_model as t:
            start_time = floor(time.time())
            current_adventure = self.storage_model.get_current_adventure(user_id)
            report = None
            if current_adventure is not None:
                report = self.update_adventure(user_id, current_adventure)
                assert report is not None
                # Offset end / start times for adventures to avoid overlap
                start_time = report.end_time + 1
            t.start_adventure(user_id, zone_id, start_time)
        return report

    def update_adventure(
        self, user_id: int, adventure: Adventure | None = None
    ) -> AdventureReport | None:
        player_items = self.get_player_items(user_id)
        if adventure is None:
            adventure = self.get_adventure_info(user_id)
        if adventure is None:
            return None
        report = process_adventure(
            player_items=player_items,
            open_quest_ids=[],
            locked_quests=set(),
            adventure=adventure,
        )
        with self.storage_model as t:
            t.update_adventure(adventure.adventure_id, report.end_time)
            for adventure_group in report.adventure_groups:
                for adventure_step in adventure_group.steps:
                    for item_id, quantity in adventure_step.items_gained.tags.items():
                        t.add_remove_tag(user_id, TagType.ITEM, item_id, quantity)
                    for item_id, quantity in adventure_step.items_lost.tags.items():
                        t.add_remove_tag(user_id, TagType.ITEM, item_id, -quantity)
                    for zone_id in adventure_step.zones_discovered:
                        t.add_zone_access(user_id, zone_id)
        return report

    def add_zone_access(self, user_id: int, zone_id: str):
        with self.storage_model as t:
            t.add_zone_access(user_id, zone_id)

    def get_player_items(self, user_id: int) -> Inventory:
        return self.storage_model.get_player_tags(user_id=user_id).get_inventory(
            TagType.ITEM
        )

    def get_adventure_info(self, user_id: int) -> Adventure | None:
        return self.storage_model.get_current_adventure(user_id)

    def get_player_zone_access(self, user_id: int) -> set[str]:
        return set(self.storage_model.get_player_zone_access(user_id))
