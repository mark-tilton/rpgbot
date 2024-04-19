import yaml
from dataclasses import dataclass
from typing import List, Optional
from game.items import ITEM_FORMAT_DICT

@dataclass
class QuestItemRequirement:
    item_id: int
    quantity: int
    consume: bool

@dataclass
class QuestReward:
    item_id: int
    quantity: tuple[int, int]
    chance: float

@dataclass
class QuestNextStep:
    step_id: int
    chance: float

@dataclass
class QuestStep:
    step_id: int
    zone_id: int
    prompt: str
    frequency: Optional[float]
    requirements: List[QuestItemRequirement]
    rewards: List[QuestReward]
    next_steps: List[QuestNextStep]

# TODO Add quest file validation to check for duplicated ids, extra fields, etc...

def load_quests() -> List[QuestStep]:
    with open("data/quests.yaml", mode="r") as f:
        quest_list_yaml = yaml.safe_load(f)
    quest_steps = []
    for quest_step_yaml in quest_list_yaml:
        id = quest_step_yaml["step"]
        zone = quest_step_yaml["zone"]
        prompt = quest_step_yaml["prompt"].format(**ITEM_FORMAT_DICT)
        frequency = quest_step_yaml.get("frequency", None)
        requirements = []
        for quest_requirement_yaml in quest_step_yaml.get("reqs", []):
            item_id = quest_requirement_yaml["item"]
            quantity = quest_requirement_yaml.get("quantity", 1)
            consume = quest_requirement_yaml.get("consume", False)
            quest_requirement = QuestItemRequirement(item_id, quantity, consume)
            requirements.append(quest_requirement)
        rewards = []
        for quest_reward_yaml in quest_step_yaml.get("rewards", []):
            item_id = quest_reward_yaml["item"]
            quantity = quest_reward_yaml.get("quantity", 1)
            if isinstance(quantity, int):
                quantity = [quantity, quantity]
            quantity = tuple(quantity)
            chance = quest_reward_yaml.get("chance", 100)
            quest_reward = QuestReward(item_id, quantity, chance)
            rewards.append(quest_reward)
        next_steps = []
        for next_step_yaml in quest_step_yaml.get("next", []):
            step_id = next_step_yaml["step"]
            chance = next_step_yaml.get("chance", 100)
            next_step = QuestNextStep(step_id, chance)
            next_steps.append(next_step)
        quest_step = QuestStep(
            step_id=id,
            zone_id=zone,
            prompt=prompt,
            frequency=frequency,
            requirements=requirements,
            rewards=rewards,
            next_steps=next_steps
        )
        quest_steps.append(quest_step)
    quest_steps.sort(key=lambda step: step.step_id)
    return quest_steps

QUESTS = load_quests()
ROOT_QUESTS = [quest for quest in QUESTS if quest.frequency is not None]
