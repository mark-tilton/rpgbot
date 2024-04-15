from dataclasses import dataclass
from enum import Enum
from typing import Dict

from items import Item


@dataclass
class Skills:
    combat_xp: int
    woodcutting_xp: int
    mining_xp: int

class ActivityType(Enum):
    COMBAT = 1
    WOODCUTTING = 2
    MINING = 3

@dataclass
class Activity:
    activity_type: ActivityType
    start_tick: int
    channel_id: int
    message_id: int

@dataclass
class ActivityReward:
    experience: Skills
    items: Dict[Item, int]
