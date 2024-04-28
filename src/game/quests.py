import os
import random
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import yaml

from .tags import TagCollection, TagType
from .items import ITEMS
from .zones import ZONES


@dataclass(frozen=True)
class QuestRequirement:
    tag_type: TagType
    tag: str
    quantity: int
    consume: bool


@dataclass(frozen=True)
class QuestReward:
    tag_type: TagType
    tag: str
    quantity: tuple[int, int]
    chance: float


@dataclass(frozen=True)
class CompletedQuest:
    quest_id: str
    tags_gained: TagCollection
    tags_lost: TagCollection
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
    requirements: list[QuestRequirement]
    rewards: list[QuestReward]
    zone_unlocks: list[str]
    next_steps: list[QuestNextStep]

    def complete_quest(self) -> CompletedQuest:
        tags_gained = TagCollection()
        for quest_reward in self.rewards:
            if random.random() * 100 >= quest_reward.chance:
                continue
            quantity = random.randint(*quest_reward.quantity)
            tags_gained.add_tag(quest_reward.tag_type, quest_reward.tag, quantity)
        tags_lost = TagCollection()
        for req in self.requirements:
            if not req.consume:
                continue
            tags_lost.add_tag(req.tag_type, req.tag, req.quantity)
        return CompletedQuest(
            quest_id=self.quest_id,
            tags_gained=tags_gained,
            tags_lost=tags_lost,
            zones_discovered=self.zone_unlocks,
        )

    def check_quest_requirements(
        self, player_tags: TagCollection, zone_id: str
    ) -> bool:
        if zone_id != self.zone_id:
            return False
        for tag_req in self.requirements:
            player_quantity = player_tags.get_quantity(tag_req.tag_type, tag_req.tag)
            if tag_req.quantity == 0 and player_quantity > 0:
                return False
            if player_quantity < tag_req.quantity:
                return False
        return True

    def choose_next_step(
        self, player_tags: TagCollection, zone_id: str
    ) -> "Quest | None":
        for step in self.next_steps:
            quest = QUESTS[step.quest_id]
            if not quest.check_quest_requirements(player_tags, zone_id):
                continue
            if random.random() * 100 < step.chance:
                return quest
        return None


# TODO Add quest file validation to check for
# duplicated ids, extra fields, etc...
def parse_tag(yaml_dict: dict[str, Any]) -> tuple[TagType, str]:
    for tag_type in TagType:
        tag = yaml_dict.get(tag_type.value)
        if tag is None:
            continue
        if tag_type == TagType.ITEM and tag not in ITEMS:
            raise Exception(f"Invalid item_id found: {tag}")
        return tag_type, tag
    raise Exception("Failed to parse tag type from quest yaml")


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

        requirements: list[QuestRequirement] = []
        for quest_requirement_yaml in quest_yaml.get("reqs", []):
            req_tag_type, req_tag = parse_tag(quest_requirement_yaml)
            req_quantity: int = quest_requirement_yaml.get("quantity", 1)
            consume: bool = quest_requirement_yaml.get("consume", False)
            quest_requirement = QuestRequirement(
                req_tag_type, req_tag, req_quantity, consume
            )
            requirements.append(quest_requirement)

        rewards: list[QuestReward] = []
        zone_unlocks: list[str] = []
        for quest_reward_yaml in quest_yaml.get("rewards", []):
            # Attempt to grab zone reward
            zone_id: str | None = quest_reward_yaml.get("zone")
            if zone_id is not None:
                zone_unlocks.append(zone_id)
                if zone_id not in ZONES:
                    raise Exception(f"Invalid zone_id found: {zone_id}")
                continue

            # Grab tag rewards
            rew_tag_type, rew_tag = parse_tag(quest_reward_yaml)
            quantity: int | tuple[int, int] = quest_reward_yaml.get("quantity", 1)
            if isinstance(quantity, int):
                quantity = (quantity, quantity)
            chance: float = quest_reward_yaml.get("chance", 100)
            quest_reward = QuestReward(rew_tag_type, rew_tag, quantity, chance)
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
