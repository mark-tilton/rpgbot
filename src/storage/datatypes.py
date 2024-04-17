from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from storage.items import Item


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
    items: Mapping[Item, int]
