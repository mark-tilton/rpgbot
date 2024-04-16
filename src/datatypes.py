from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional

from items import Item


@dataclass
class Skills:
    combat_xp: int = 0
    woodcutting_xp: int = 0
    mining_xp: int = 0

class ActivityType(Enum):
    IDLE = 0
    COMBAT = 1
    WOODCUTTING = 2
    MINING = 3

@dataclass
class Activity:
    activity_id: int
    user_id: int
    activity_type: ActivityType
    start_tick: int
    last_updated: int

@dataclass
class ActivityReward:
    experience: Skills
    items: Mapping[Item, int]
