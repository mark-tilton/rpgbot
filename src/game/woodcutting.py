import random
from typing import List, Mapping
from game.validation import ValidationResult
from storage.equipment import Equipment
from storage.activity import ActivityReward
from storage.item import ITEM_NAME, Item

LOG_TYPES = [
    Item.TEAK_LOG,
    Item.WALNUT_LOG,
    Item.PINE_LOG,
    Item.BIRCH_LOG,
    Item.OAK_LOG,
    Item.MAPLE_LOG,
    Item.MAHOGANY_LOG,
]

AXE_TYPES = [
    Item.TIN_AXE,
    Item.COPPER_AXE,
    Item.BRONZE_AXE,
    Item.IRON_AXE,
    Item.STEEL_AXE,
    Item.TITANIUM_AXE,
]

LOG_TOOL_REQUIREMENT = {
    Item.TEAK_LOG: Item.TIN_AXE,
    Item.WALNUT_LOG: Item.TIN_AXE,
    Item.PINE_LOG: Item.COPPER_AXE,
    Item.BIRCH_LOG: Item.BRONZE_AXE,
    Item.OAK_LOG: Item.IRON_AXE,
    Item.MAPLE_LOG: Item.STEEL_AXE,
    Item.MAHOGANY_LOG: Item.TITANIUM_AXE,
}

AXE_LEVEL = {
    Item.TIN_AXE: 1,
    Item.COPPER_AXE: 2,
    Item.BRONZE_AXE: 3,
    Item.IRON_AXE: 4,
    Item.STEEL_AXE: 5,
    Item.TITANIUM_AXE: 6,
}

def validate_woodcutting_activity(equipment: Equipment, log_type: Item) -> ValidationResult:
    if equipment.woodcutting_axe is None or equipment.woodcutting_axe not in AXE_LEVEL:
        return ValidationResult(False, "Must have an axe equipped to chop trees.")
    equipped_tool = equipment.woodcutting_axe
    required_tool = LOG_TOOL_REQUIREMENT[log_type]
    equipped_tool_level = AXE_LEVEL[equipped_tool]
    tool_level_required = AXE_LEVEL[required_tool]
    if equipped_tool_level < tool_level_required:
        required_tool_name = ITEM_NAME[required_tool]
        log_name = ITEM_NAME[log_type]
        return ValidationResult(False, f"Invalid tool equipped. {log_name} requires at least a {required_tool_name}.")
    return ValidationResult(True)

def process_woodcutting(ticks: int, log_type: Item) -> ActivityReward:
    if log_type not in LOG_TYPES:
        raise Exception("Invalid log type given")
    items: Mapping[Item, int] = {}
    for _ in range(ticks):
        if random.random() * 100 < 30:
            if log_type not in items:
                items[log_type] = 0
            items[log_type] += 1
    return ActivityReward(items)