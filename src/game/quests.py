import os
import random
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import yaml

from .skills import level_to_xp
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
    tags_changed: TagCollection


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
    merge: bool
    requirements: list[QuestRequirement]
    rewards: list[QuestReward]
    next_steps: list[QuestNextStep]

    def complete_quest(self) -> CompletedQuest:
        tags_changed = TagCollection()
        for quest_reward in self.rewards:
            if random.random() * 100 >= quest_reward.chance:
                continue
            quantity = random.randint(*quest_reward.quantity)
            tags_changed.add_tag(quest_reward.tag_type, quest_reward.tag, quantity)
        for req in self.requirements:
            if not req.consume:
                continue
            tags_changed.add_tag(req.tag_type, req.tag, -req.quantity)
        return CompletedQuest(quest_id=self.quest_id, tags_changed=tags_changed)

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
        if tag_type == TagType.ZONE and tag not in ZONES:
            raise Exception(f"Invalid zone_id found: {tag}")
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
        merge: bool = quest_yaml.get("merge", False)

        prompts: str | list[str] = quest_yaml.get("prompt", [])
        if isinstance(prompts, str):
            prompts = [prompts]

        requirements: list[QuestRequirement] = []
        for quest_requirement_yaml in quest_yaml.get("reqs", []):
            req_tag_type, req_tag = parse_tag(quest_requirement_yaml)
            req_quantity: int = quest_requirement_yaml.get("quantity", 1)
            if req_tag_type == TagType.LEVEL:
                req_tag_type = TagType.XP
                req_quantity = level_to_xp(req_quantity)
            consume: bool = quest_requirement_yaml.get("consume", False)
            quest_requirement = QuestRequirement(
                req_tag_type, req_tag, req_quantity, consume
            )
            requirements.append(quest_requirement)

        rewards: list[QuestReward] = []
        for quest_reward_yaml in quest_yaml.get("rewards", []):
            # Grab tag rewards
            rew_tag_type, rew_tag = parse_tag(quest_reward_yaml)
            if rew_tag_type == TagType.LEVEL:
                raise Exception("Cannot reward skill experience in levels")
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
            merge=merge,
            requirements=requirements,
            rewards=rewards,
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
