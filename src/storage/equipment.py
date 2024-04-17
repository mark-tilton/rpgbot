from dataclasses import dataclass
from enum import Enum
from typing import Optional
from storage.item import Item


class EquipmentType(Enum):
    WOODCUTTING_AXE = 1

EQUIPMENT_SLOT = {
    Item.TIN_AXE: EquipmentType.WOODCUTTING_AXE,
    Item.COPPER_AXE: EquipmentType.WOODCUTTING_AXE,
    Item.BRONZE_AXE: EquipmentType.WOODCUTTING_AXE,
    Item.IRON_AXE: EquipmentType.WOODCUTTING_AXE,
    Item.STEEL_AXE: EquipmentType.WOODCUTTING_AXE,
    Item.TITANIUM_AXE: EquipmentType.WOODCUTTING_AXE,
}


@dataclass
class Equipment:
    woodcutting_axe: Optional[Item] = None

    def get_slot(self, equipment_type: EquipmentType) -> Optional[Item]:
        if equipment_type == EquipmentType.WOODCUTTING_AXE:
            return self.woodcutting_axe
    
    def set_slot(self, equipment_type: EquipmentType, item: Item):
        if equipment_type == EquipmentType.WOODCUTTING_AXE:
            self.woodcutting_axe = item
