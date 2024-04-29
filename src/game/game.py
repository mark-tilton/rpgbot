import time
from math import floor

from storage.storagemodel import StorageModel

from .adventure import Adventure, AdventureReport, process_adventure
from .tags import TagCollection


class Game:
    def __init__(self):
        self.storage_model = StorageModel()

    def start_adventure(self, user_id: int, zone_id: str, thread_id: int) -> AdventureReport | None:
        with self.storage_model as t:
            start_time = floor(time.time())
            current_adventure = self.storage_model.get_current_adventure(user_id)
            report = None
            if current_adventure is not None:
                report = self.update_adventure(user_id, current_adventure)
                assert report is not None
                # Offset end / start times for adventures to avoid overlap
                start_time = report.end_time + 1
            t.start_adventure(user_id, zone_id, start_time, thread_id)
        return report

    def update_adventure(
        self, user_id: int, adventure: Adventure | None = None
    ) -> AdventureReport | None:
        player_tags = self.get_player_tags(user_id)
        if adventure is None:
            adventure = self.get_adventure_info(user_id)
        if adventure is None:
            return None
        report = process_adventure(
            player_tags=player_tags,
            adventure=adventure,
        )
        with self.storage_model as t:
            t.update_adventure(adventure.adventure_id, report.end_time)
            for adventure_group in report.adventure_groups:
                for adventure_step in adventure_group.steps:
                    for (
                        tag_type,
                        tag,
                        quantity,
                    ) in adventure_step.tags_gained.get_all_tags():
                        t.add_remove_tag(user_id, tag_type, tag, quantity)
                    for (
                        tag_type,
                        tag,
                        quantity,
                    ) in adventure_step.tags_lost.get_all_tags():
                        t.add_remove_tag(user_id, tag_type, tag, -quantity)
        return report

    def get_player_tags(self, user_id: int) -> TagCollection:
        return self.storage_model.get_player_tags(user_id=user_id)

    def get_adventure_info(self, user_id: int) -> Adventure | None:
        return self.storage_model.get_current_adventure(user_id)
