from dataclasses import dataclass
from math import floor, sqrt


@dataclass
class Skill:
    skill_id: str

def level_to_xp(level: int) -> int:
    return level * level * 10

def xp_to_level(xp: int) -> int:
    return floor(sqrt(xp / 10))