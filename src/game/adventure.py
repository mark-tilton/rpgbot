import time
import random
from typing import List, Optional
from dataclasses import dataclass

from game.quests import QUESTS, ROOT_QUESTS, QuestStep 
from game.items import ITEMS, Inventory


@dataclass
class AdventureStep:
    prompt: str
    items_gained: Inventory
    items_lost: Inventory

    def display(self) -> str:
        display_string = self.prompt
        if len(self.items_gained.items) > 0:
            display_string += "\n" + "\n".join([f"    +{quantity} {ITEMS[item_id].name}" 
                for item_id, quantity in self.items_gained.items.items()])
        if len(self.items_lost.items) > 0:
            display_string += "\n" + "\n".join([f"    -{quantity} {ITEMS[item_id].name}" 
                for item_id, quantity in self.items_lost.items.items()])
        return display_string


@dataclass
class AdventureReport:
    start_time: int
    end_time: int
    adventure_steps: List[AdventureStep]
    open_quests: List[int]

    def display(self) -> str:
        return "\n".join([step.display() for step in self.adventure_steps])


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
TICK_RATE = 0.5 # One tick every 5 seconds

def check_step_requirements(
    quest_step: QuestStep, 
    player_items: Inventory, 
    zone_id: int) -> bool:
    if zone_id != quest_step.zone_id:
        return False
    for item_req in quest_step.requirements:
        player_quantity = player_items.items.get(item_req.item_id, 0)
        if item_req.quantity == 0 and player_quantity > 0:
            return False
        if player_quantity < item_req.quantity:
            return False
    return True

def try_progress_step(
    step_id: int, 
    player_items: Inventory, 
    zone_id: int) -> QuestCompletion:
    quest = QUESTS[step_id]

    # Can't progress a quest that doesn't have next steps
    if len(quest.next_steps) == 0:
        return QuestCompletion(None, None)
    
    # Choose a next step
    next_step = None
    for step in quest.next_steps:
        step_quest = QUESTS[step.step_id]
        if not check_step_requirements(step_quest, player_items, zone_id):
            continue
        if random.random() * 100 < step.chance:
            next_step = step_quest
            break
    
    # Unable to progress this quest
    if next_step is None:
        return QuestCompletion(None, step_id)
    
    # Roll for items
    rewards = Inventory()
    for reward in next_step.rewards:
        if random.random() * 100 < reward.chance:
            quantity = random.randint(*reward.quantity)
            rewards.add_item(reward.item_id, quantity)
    
    # Consume items
    consumed_items = Inventory()
    for item_req in next_step.requirements:
        if not item_req.consume:
            continue
        consumed_items.add_item(item_req.item_id, item_req.quantity)

    # Check if step is terminal
    next_step_id = None
    if len(next_step.next_steps) > 0:
        next_step_id = next_step.step_id

    adventure_step = AdventureStep(next_step.prompt, rewards, consumed_items)
    return QuestCompletion(adventure_step, next_step_id)

def process_adventure(
    player_items: Inventory, 
    open_quests: List[int],
    zone_id: int, 
    adventure: Adventure) -> AdventureReport:
    current_time = int(time.time())
    elapsed = current_time - adventure.last_updated
    num_ticks = int(elapsed / TICK_RATE)
    current_time = adventure.last_updated + num_ticks * TICK_RATE

    open_quests = [*open_quests]

    adventure_steps: List[AdventureStep] = []
    for tick in range(num_ticks):
        # Check if we can progress any open quests
        completed_step_idx = None
        quest_adventure_step = None
        next_step_id = None
        for i, step_id in reversed(list(enumerate(open_quests))):
            result = try_progress_step(step_id, player_items, zone_id)
            if result.adventure_step is not None:
                completed_step_idx = i
                quest_adventure_step = result.adventure_step
                next_step_id = result.next_step
                break
        if completed_step_idx is not None and quest_adventure_step is not None:
            open_quests.pop(completed_step_idx)
            for item, quantity in quest_adventure_step.items_gained.items.items():
                player_items.add_item(item, quantity)
            for item, quantity in quest_adventure_step.items_lost.items.items():
                player_items.remove_item(item, quantity)
            adventure_steps.append(quest_adventure_step)
            if next_step_id is not None:
                open_quests.append(next_step_id)
            continue

        # Try to start a new quest
        new_quest = None
        for root_quest in ROOT_QUESTS:
            if not check_step_requirements(root_quest, player_items, zone_id):
                continue
            frequency_seconds = root_quest.frequency * 60
            frequency_ticks = frequency_seconds / TICK_RATE
            # if random.random() < (1 / frequency_ticks):
            if random.random() < 0.2:
                new_quest = root_quest
                break
        
        if new_quest is not None:
            items_gained = Inventory()
            for quest_reward in new_quest.rewards:
                quantity = random.randint(*quest_reward.quantity)
                items_gained.add_item(quest_reward.item_id, quantity)
                player_items.add_item(quest_reward.item_id, quantity)
            items_lost = Inventory()
            for req in new_quest.requirements:
                if not req.consume:
                    continue
                items_lost.add_item(req.item_id, req.quantity)
                player_items.remove_item(req.item_id, req.quantity)
            adventure_steps.append(AdventureStep(new_quest.prompt, items_gained, items_lost))
            if len(new_quest.next_steps) > 0:
                open_quests.append(new_quest.step_id)
            continue

    return AdventureReport(adventure.last_updated, current_time, adventure_steps, open_quests)

