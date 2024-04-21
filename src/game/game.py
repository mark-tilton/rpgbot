import time
from math import floor

from storage.storagemodel import StorageModel

from game.adventure import Adventure, AdventureReport, process_adventure
from game.items import Inventory


class Game:
    def __init__(self):
        self.storage_model = StorageModel()

    def start_adventure(self, user_id: int, zone_id: int) -> AdventureReport | None:
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
            t.set_player_zone(user_id, zone_id, start_time)
        return report

    def update_adventure(
        self, user_id: int, adventure: Adventure | None = None
    ) -> AdventureReport | None:
        player_items = self.get_player_items(user_id)
        open_quests = self.get_open_quests(user_id)
        zone_id = self.get_player_zone(user_id)
        if adventure is None:
            adventure = self.get_adventure_info(user_id)
        if adventure is None or zone_id is None:
            return None
        finished_quests = self.get_finished_quests(user_id)
        report = process_adventure(
            player_items=player_items,
            open_quest_ids=open_quests,
            zone_id=zone_id,
            locked_quests=finished_quests,
            adventure=adventure,
        )
        with self.storage_model as t:
            t.update_adventure(adventure.adventure_id, report.end_time)
            for adventure_step in report.adventure_steps:
                for item_id, quantity in adventure_step.items_gained.items.items():
                    t.add_remove_item(user_id, item_id, quantity)
                for item_id, quantity in adventure_step.items_lost.items.items():
                    t.add_remove_item(user_id, item_id, -quantity)
                for zone_id in adventure_step.zones_discovered:
                    t.add_zone_access(user_id, zone_id)
            for finished_quest in report.finished_quests:
                t.add_finished_quest(user_id, finished_quest)
            t.set_open_quests(user_id, report.open_quests)
        return report

    def add_zone_access(self, user_id: int, zone_id: int):
        with self.storage_model as t:
            t.add_zone_access(user_id, zone_id)

    def add_finished_quests(self, user_id: int, quest_id: int):
        with self.storage_model as t:
            t.add_finished_quest(user_id, quest_id)

    def get_player_items(self, user_id: int) -> Inventory:
        return Inventory(dict(self.storage_model.get_player_items(user_id=user_id)))

    def get_open_quests(self, user_id: int) -> list[int]:
        return self.storage_model.get_open_quests(user_id)

    def get_player_zone(self, user_id: int) -> int | None:
        return self.storage_model.get_player_zone(user_id)

    def get_adventure_info(self, user_id: int) -> Adventure | None:
        return self.storage_model.get_current_adventure(user_id)

    def get_player_zone_access(self, user_id: int) -> set[int]:
        return set(self.storage_model.get_player_zone_access(user_id))

    def get_finished_quests(self, user_id: int) -> set[int]:
        return set(self.storage_model.get_finished_quests(user_id))
