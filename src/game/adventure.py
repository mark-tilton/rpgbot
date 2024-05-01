import random
import time
from collections.abc import Mapping
from dataclasses import dataclass, field

from .items import ITEMS
from .quests import ROOT_QUESTS, Quest
from .tags import Inventory, TagCollection, TagType
from .zones import ZONES


@dataclass
class AdventureStep:
    quest: Quest
    tags_gained: TagCollection = field(default_factory=TagCollection)
    tags_lost: TagCollection = field(default_factory=TagCollection)

    def get_discovered_zones(self) -> list[str]:
        return [
            zone_id
            for zone_id, quantity in self.tags_gained.get_inventory(
                TagType.ZONE
            ).get_all_tags()
            if quantity >= 1
        ]

    def display(self) -> str:
        display_lines = []
        for prompt in self.quest.prompts:
            display_lines = [f"> - {prompt}  "]
        inventories: list[tuple[str, Inventory]] = [
            ("+", self.tags_gained.get_inventory(TagType.ITEM)),
            ("-", self.tags_lost.get_inventory(TagType.ITEM)),
        ]
        for sign, inventory in inventories:
            for item_id, quantity in inventory.get_all_tags():
                item = ITEMS[item_id]
                item_name = item.name if quantity == 1 else item.plural
                item_name = item_name.title()
                display_lines.append(f">     {sign}{quantity} {item_name}  ")
        for skill_id, xp in self.tags_gained.get_inventory(TagType.XP).get_all_tags():
            display_lines.append(f">     Gained {xp} {skill_id} xp  ")
        for zone_id in self.get_discovered_zones():
            zone = ZONES[zone_id]
            display_lines.append(f">     Discovered zone: {zone.name.title()}  ")
        return "\n".join(display_lines)


@dataclass
class AdventureGroup:
    steps: list[AdventureStep]
    message_id: int | None = None

    @property
    def merge(self) -> bool:
        return any(step.quest.merge for step in self.steps)

    @property
    def group_id(self) -> str:
        return ",".join(step.quest.quest_id for step in self.steps)

    def display(self) -> str: ...


@dataclass
class Adventure:
    adventure_id: int
    user_id: int
    zone_id: str
    last_updated: int
    thread_id: int


@dataclass
class AdventureReport:
    start_time: int
    end_time: int
    adventure_groups: list[AdventureGroup]
    adventure: Adventure

    def display(self) -> str:
        merged_steps: Mapping[str, list[AdventureStep]] = {}
        display_lines: list[str] = []
        for adventure_group in self.adventure_groups:
            group_gap = False
            for step in adventure_group.steps:
                if step.quest.merge:
                    if step.quest.quest_id not in merged_steps:
                        merged_steps[step.quest.quest_id] = []
                    merged_steps[step.quest.quest_id].append(step)
                    continue
                group_gap = True
                display_lines.append(step.display())
            if group_gap:
                display_lines.append("")
        for _, steps in merged_steps.items():
            first_step = steps[0]
            merged_step = AdventureStep(first_step.quest)
            for step in steps:
                merged_step.tags_gained.add_tag_collection(step.tags_gained)
                merged_step.tags_lost.add_tag_collection(step.tags_lost)
            display_lines.append(merged_step.display())

        return "\n".join(display_lines)


@dataclass
class QuestCompletion:
    adventure_step: AdventureStep | None
    next_step: int | None


# TODO Change all rates to be based on tick rate so
# you can speed up / slow down the game.
TICK_RATE = 1  # One tick every 1 second


def process_adventure(
    player_tags: TagCollection,
    adventure: Adventure,
) -> AdventureReport:
    current_time = int(time.time())
    elapsed = current_time - adventure.last_updated
    num_ticks = int(elapsed / TICK_RATE)
    current_time = adventure.last_updated + num_ticks * TICK_RATE

    zone_id = adventure.zone_id

    adventure_groups: list[AdventureGroup] = []
    for _ in range(num_ticks):
        # Try to start a new quest
        new_quests: list[Quest] = []
        for root_quest, frequency in ROOT_QUESTS:
            if not root_quest.check_quest_requirements(player_tags, zone_id):
                continue
            frequency_seconds = frequency * 60
            frequency_ticks = frequency_seconds / TICK_RATE
            threshold = 1 / frequency_ticks if frequency_ticks > 0 else 1
            int_threshold = int(threshold)
            threshold -= int_threshold
            for _ in range(int_threshold):
                new_quests.append(root_quest)
            if random.random() < threshold:
                new_quests.append(root_quest)

        for new_root in new_quests:
            quest_queue = [new_root]
            adventure_steps: list[AdventureStep] = []
            while len(quest_queue) > 0:
                new_quest = quest_queue.pop()
                completed_quest = new_quest.complete_quest()
                player_tags.add_tag_collection(completed_quest.tags_gained)
                # We can assume this remove will succeed because we already checked requirements
                player_tags.remove_tag_collection(completed_quest.tags_lost)
                adventure_steps.append(
                    AdventureStep(
                        quest=new_quest,
                        tags_gained=completed_quest.tags_gained,
                        tags_lost=completed_quest.tags_lost,
                    )
                )
                next_step = new_quest.choose_next_step(player_tags, zone_id)
                if next_step is None:
                    continue
                quest_queue.append(next_step)

            if len(adventure_steps) > 0:
                adventure_groups.append(AdventureGroup(adventure_steps))

    return AdventureReport(
        adventure.last_updated,
        current_time,
        adventure_groups,
        adventure,
    )
