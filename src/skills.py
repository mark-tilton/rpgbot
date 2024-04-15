
from dataclasses import dataclass
from math import floor


def get_level(xp: int) -> int:
    return floor(xp / 1000) + 1

def get_xp(level: int) -> int:
    ...