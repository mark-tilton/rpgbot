import time
import random
from typing import List, Mapping, Optional
from dataclasses import dataclass, field

from game.quests import QUESTS, ROOT_QUESTS, Quest 
from game.items import ITEMS, Inventory

@dataclass
class AdventureStep:
    quest: Quest
    items_gained: Inventory = field(default_factory=Inventory)
    items_lost: Inventory = field(default_factory=Inventory)

    def display(self) -> str:
        display_lines = [self.quest.prompt]
        inventories: List[tuple[str, Inventory]] = [("+", self.items_gained), ("-", self.items_lost)]
        for sign, inventory in inventories:
            for item_id, quantity in inventory.items.items():
                item = ITEMS[item_id]
                item_name = item.name if quantity == 1 else item.plural
                item_name = item_name.title()
                display_lines.append(f"    {sign}{quantity} {item_name}")
        return "\n".join(display_lines)


@dataclass
class AdventureReport:
    start_time: int
    end_time: int
    adventure_steps: List[AdventureStep]
    open_quests: List[int]

    def display(self) -> str:
        merged_steps: Mapping[int, List[AdventureStep]] = {}
        display_lines: List[str] = []
        for step in self.adventure_steps:
            if step.quest.merge:
                if step.quest.quest_id not in merged_steps:
                    merged_steps[step.quest.quest_id] = []
                merged_steps[step.quest.quest_id].append(step)
                continue
            display_lines.append(step.display())
        for _, steps in merged_steps.items():
            first_step = steps[0]
            merged_step = AdventureStep(first_step.quest)
            for step in steps:
                for item, quantity in step.items_gained.items.items():
                    merged_step.items_gained.add_item(item, quantity)
                for item, quantity in step.items_lost.items.items():
                    merged_step.items_lost.add_item(item, quantity)
            display_lines.append(merged_step.display())

        return "\n".join(display_lines)


@dataclass
class QuestCompletion:
    adventure_step: Optional[AdventureStep]
    next_step: Optional[int]


@dataclass
class Adventure:
    adventure_id: int
    user_id: int
    zone_id: int
    last_updated: int


# TODO Change all rates to be based on tick rate so you can speed up / slow down the game.
TICK_RATE = 5 # One tick every 5 seconds

def process_quests(
    quests: List[Quest], 
    player_items: Inventory, 
    zone_id: int) -> tuple[List[AdventureStep], List[Quest]]:
    adventure_steps: List[AdventureStep] = []
    open_quests: List[Quest] = []
    while len(quests) > 0:
        new_quest = quests.pop()
        completed_quest = new_quest.complete_quest()
        player_items.add_inventory(completed_quest.items_gained)
        player_items.remove_inventory(completed_quest.items_lost)
        adventure_steps.append(AdventureStep(new_quest, completed_quest.items_gained, completed_quest.items_lost))
        next_step = new_quest.choose_next_step(player_items, zone_id)
        if next_step is None:
            if new_quest.hold_open:
                open_quests.append(new_quest)
            continue
        quests.append(next_step)
    return adventure_steps, open_quests

def process_adventure(
    player_items: Inventory, 
    open_quest_ids: List[int],
    zone_id: int, 
    adventure: Adventure) -> AdventureReport:
    current_time = int(time.time())
    elapsed = current_time - adventure.last_updated
    num_ticks = int(elapsed / TICK_RATE)
    current_time = adventure.last_updated + num_ticks * TICK_RATE

    open_quests = [QUESTS[quest_id] for quest_id in open_quest_ids]

    adventure_steps: List[AdventureStep] = []
    for _ in range(num_ticks):
        available_quests: List[Quest] = []
        removed_open_quests: List[int] = []
        for i, open_quest in enumerate(reversed(open_quests)):
            next_quest = open_quest.choose_next_step(player_items, zone_id)
            if next_quest is None:
                continue
            removed_open_quests.append(len(open_quests) - i - 1)
            available_quests.append(next_quest)
        if len(removed_open_quests) > 0:
            print(removed_open_quests)
        for i in removed_open_quests:
            open_quests.pop(i)
        
        new_adventure_steps, new_open_quests = process_quests(available_quests, player_items, zone_id)
        open_quests.extend(new_open_quests)
        adventure_steps.extend(new_adventure_steps)

        # Try to start a new quest
        new_quests: List[Quest] = []
        for root_quest, frequency in ROOT_QUESTS:
            if not root_quest.check_quest_requirements(player_items, zone_id):
                continue
            frequency_seconds = frequency * 60
            frequency_ticks = frequency_seconds / TICK_RATE
            threshold = 1 / frequency_ticks if frequency_ticks > 0 else 1
            if random.random() < threshold:
                new_quests.append(root_quest)

        new_adventure_steps, new_open_quests = process_quests(new_quests, player_items, zone_id)
        open_quests.extend(new_open_quests)
        adventure_steps.extend(new_adventure_steps)

    return AdventureReport(
        adventure.last_updated, 
        current_time, 
        adventure_steps, 
        [quest.quest_id for quest in open_quests])

