import os
import random
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import yaml

from .tags import Inventory
from .items import ITEMS
from .zones import ZONES


@dataclass(frozen=True)
class QuestItemRequirement:
    item_id: str
    quantity: int
    consume: bool


@dataclass(frozen=True)
class QuestReward:
    item_id: str
    quantity: tuple[int, int]
    chance: float


@dataclass(frozen=True)
class CompletedQuest:
    quest_id: str
    items_gained: Inventory
    items_lost: Inventory
    zones_discovered: list[str]


@dataclass(frozen=True)
class QuestNextStep:
    quest_id: str
    chance: float


@dataclass(frozen=True)
class Quest:
    quest_id: str
    zone_id: str
    prompts: list[str]
    frequency: float | None
    repeatable: bool
    merge: bool
    hold_open: bool
    requirements: list[QuestItemRequirement]
    rewards: list[QuestReward]
    zone_unlocks: list[str]
    next_steps: list[QuestNextStep]

    def complete_quest(self) -> CompletedQuest:
        items_gained = Inventory()
        for quest_reward in self.rewards:
            if random.random() * 100 >= quest_reward.chance:
                continue
            quantity = random.randint(*quest_reward.quantity)
            items_gained.add_tag(quest_reward.item_id, quantity)
        items_lost = Inventory()
        for req in self.requirements:
            if not req.consume:
                continue
            items_lost.add_tag(req.item_id, req.quantity)
        return CompletedQuest(
            quest_id=self.quest_id,
            items_gained=items_gained,
            items_lost=items_lost,
            zones_discovered=self.zone_unlocks,
        )

    def check_quest_requirements(self, player_items: Inventory, zone_id: str) -> bool:
        if zone_id != self.zone_id:
            return False
        for item_req in self.requirements:
            player_quantity = player_items.tags.get(item_req.item_id, 0)
            if item_req.quantity == 0 and player_quantity > 0:
                return False
            if player_quantity < item_req.quantity:
                return False
        return True

    def choose_next_step(self, player_items: Inventory, zone_id: str) -> "Quest | None":
        for step in self.next_steps:
            quest = QUESTS[step.quest_id]
            if not quest.check_quest_requirements(player_items, zone_id):
                continue
            if random.random() * 100 < step.chance:
                return quest
        return None


# TODO Add quest file validation to check for
# duplicated ids, extra fields, etc...
def load_quests() -> Mapping[str, Quest]:
    zone_dir = "data/zones"
    files = os.listdir(zone_dir)
    quest_files: list[list[dict[str, Any]]] = []
    for file in files:
        with open(f"{zone_dir}/{file}", mode="r") as f:
            quest_files.append(yaml.safe_load(f))

    quest_list_yaml = [quest for file in quest_files for quest in file]

    quests: dict[str, Quest] = {}
    for quest_yaml in quest_list_yaml:
        quest_id: str = quest_yaml["quest"]
        zone: str = quest_yaml["zone"]
        frequency: float = quest_yaml.get("frequency", None)
        repeatable: bool = quest_yaml.get("repeatable", True)
        merge: bool = quest_yaml.get("merge", False)
        hold_open: bool = quest_yaml.get("hold_open", False)

        prompts: str | list[str] = quest_yaml.get("prompt", [])
        if isinstance(prompts, str):
            prompts = [prompts]

        requirements: list[QuestItemRequirement] = []
        for quest_requirement_yaml in quest_yaml.get("reqs", []):
            req_item_id: str = quest_requirement_yaml["item"]
            if req_item_id not in ITEMS:
                raise Exception(f"Invalid item_id found: {req_item_id}")
            req_quantity: int = quest_requirement_yaml.get("quantity", 1)
            consume: bool = quest_requirement_yaml.get("consume", False)
            quest_requirement = QuestItemRequirement(req_item_id, req_quantity, consume)
            requirements.append(quest_requirement)

        rewards: list[QuestReward] = []
        zone_unlocks: list[str] = []
        for quest_reward_yaml in quest_yaml.get("rewards", []):
            item_id: str | None = quest_reward_yaml.get("item", None)
            if item_id is None:
                zone_id: str = quest_reward_yaml["zone"]
                if zone_id not in ZONES:
                    raise Exception(f"Invalid zone_id found: {zone_id}")
                zone_unlocks.append(zone_id)
                continue
            if item_id not in ITEMS:
                raise Exception(f"Invalid item_id found: {item_id}")
            quantity: int | tuple[int, int] = quest_reward_yaml.get("quantity", 1)
            if isinstance(quantity, int):
                quantity = (quantity, quantity)
            chance: float = quest_reward_yaml.get("chance", 100)
            quest_reward = QuestReward(item_id, quantity, chance)
            rewards.append(quest_reward)

        next_steps: list[QuestNextStep] = []
        for next_step_yaml in quest_yaml.get("next", []):
            next_quest_id: str = next_step_yaml["quest"]
            chance: float = next_step_yaml.get("chance", 100)
            next_step = QuestNextStep(next_quest_id, chance)
            next_steps.append(next_step)

        quest = Quest(
            quest_id=quest_id,
            zone_id=zone,
            prompts=prompts,
            frequency=frequency,
            repeatable=repeatable,
            merge=merge,
            hold_open=hold_open,
            requirements=requirements,
            rewards=rewards,
            zone_unlocks=zone_unlocks,
            next_steps=next_steps,
        )
        if quest_id in quests:
            raise Exception(f"Duplicate quest id found: {quest_id}")
        quests[quest_id] = quest
    return quests


QUESTS = load_quests()
ROOT_QUESTS = [
    (quest, quest.frequency)
    for _, quest in QUESTS.items()
    if quest.frequency is not None
]
