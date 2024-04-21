import random
from dataclasses import dataclass
from typing import List, Mapping, Optional

import yaml

from .items import ITEM_FORMAT_DICT, Inventory


@dataclass(frozen=True)
class QuestItemRequirement:
    item_id: int
    quantity: int
    consume: bool


@dataclass(frozen=True)
class QuestReward:
    item_id: int
    quantity: tuple[int, int]
    chance: float


@dataclass(frozen=True)
class CompletedQuest:
    quest_id: int
    items_gained: Inventory
    items_lost: Inventory
    zones_discovered: List[int]


@dataclass(frozen=True)
class QuestNextStep:
    quest_id: int
    chance: float


@dataclass(frozen=True)
class Quest:
    quest_id: int
    zone_id: int
    prompt: str
    frequency: Optional[float]
    merge: bool
    hold_open: bool
    requirements: List[QuestItemRequirement]
    rewards: List[QuestReward]
    zone_unlocks: List[int]
    next_steps: List[QuestNextStep]

    def complete_quest(self) -> CompletedQuest:
        items_gained = Inventory()
        for quest_reward in self.rewards:
            quantity = random.randint(*quest_reward.quantity)
            items_gained.add_item(quest_reward.item_id, quantity)
        items_lost = Inventory()
        for req in self.requirements:
            if not req.consume:
                continue
            items_lost.add_item(req.item_id, req.quantity)
        zones_discovered = []
        return CompletedQuest(
            quest_id=self.quest_id,
            items_gained=items_gained,
            items_lost=items_lost,
            zones_discovered=zones_discovered,
        )

    def check_quest_requirements(self, player_items: Inventory, zone_id: int) -> bool:
        if zone_id != self.zone_id:
            return False
        for item_req in self.requirements:
            player_quantity = player_items.items.get(item_req.item_id, 0)
            if item_req.quantity == 0 and player_quantity > 0:
                return False
            if player_quantity < item_req.quantity:
                return False
        return True

    def choose_next_step(
        self, player_items: Inventory, zone_id: int
    ) -> Optional["Quest"]:
        for step in self.next_steps:
            quest = QUESTS[step.quest_id]
            if not quest.check_quest_requirements(player_items, zone_id):
                continue
            if random.random() * 100 < step.chance:
                return quest
        return None


# TODO Add quest file validation to check for
# duplicated ids, extra fields, etc...
def load_quests() -> Mapping[int, Quest]:
    with open("data/quests.yaml", mode="r") as f:
        quest_list_yaml = yaml.safe_load(f)

    quests: dict[int, Quest] = {}
    for quest_yaml in quest_list_yaml:
        quest_id = quest_yaml["quest"]
        zone = quest_yaml["zone"]
        prompt = quest_yaml["prompt"].format(**ITEM_FORMAT_DICT)
        frequency = quest_yaml.get("frequency", None)
        merge = quest_yaml.get("merge", False)
        hold_open = quest_yaml.get("hold_open", False)

        requirements: List[QuestItemRequirement] = []
        for quest_requirement_yaml in quest_yaml.get("reqs", []):
            item_id = quest_requirement_yaml["item"]
            quantity = quest_requirement_yaml.get("quantity", 1)
            consume = quest_requirement_yaml.get("consume", False)
            quest_requirement = QuestItemRequirement(
                item_id, quantity, consume)
            requirements.append(quest_requirement)

        rewards: List[QuestReward] = []
        zone_unlocks: List[int] = []
        for quest_reward_yaml in quest_yaml.get("rewards", []):
            item_id = quest_reward_yaml.get("item", None)
            if item_id is None:
                zone_id = quest_reward_yaml["zone"]
                zone_unlocks.append(zone_id)
                continue
            quantity = quest_reward_yaml.get("quantity", 1)
            if isinstance(quantity, int):
                quantity = [quantity, quantity]
            quantity = (quantity[0], quantity[1])
            chance = quest_reward_yaml.get("chance", 100)
            quest_reward = QuestReward(item_id, quantity, chance)
            rewards.append(quest_reward)

        next_steps: List[QuestNextStep] = []
        for next_step_yaml in quest_yaml.get("next", []):
            next_quest_id = next_step_yaml["quest"]
            chance = next_step_yaml.get("chance", 100)
            next_step = QuestNextStep(next_quest_id, chance)
            next_steps.append(next_step)

        quest = Quest(
            quest_id=quest_id,
            zone_id=zone,
            prompt=prompt,
            frequency=frequency,
            merge=merge,
            hold_open=hold_open,
            requirements=requirements,
            rewards=rewards,
            zone_unlocks=zone_unlocks,
            next_steps=next_steps,
        )
        quests[quest_id] = quest
    return quests


QUESTS = load_quests()
ROOT_QUESTS = [
    (quest, quest.frequency)
    for _, quest in QUESTS.items()
    if quest.frequency is not None
]
