from dataclasses import dataclass, field
from enum import Enum


class TagType(Enum):
    ITEM = "item"
    TAG = "tag"
    ZONE = "zone"
    XP = "xp"
    LEVEL = "level"


@dataclass
class Inventory:
    _tags: dict[str, int] = field(default_factory=dict)

    def get_quantity(self, tag: str) -> int:
        return self._tags.get(tag, 0)

    def add_tag(self, tag: str, quantity: int):
        if quantity == 0:
            return
        if tag not in self._tags:
            self._tags[tag] = quantity
            return
        self._tags[tag] += quantity

    #TODO: Remove this and use negative quantities
    def remove_tag(self, tag: str, quantity: int) -> bool:
        if quantity <= 0:
            return True
        if tag not in self._tags:
            return False
        current_quantity = self._tags[tag]
        if current_quantity < quantity:
            return False
        self._tags[tag] = current_quantity - quantity
        return True

    def add_inventory(self, inventory: "Inventory"):
        for tag, quantity in inventory._tags.items():
            self.add_tag(tag, quantity)

    def remove_inventory(self, inventory: "Inventory") -> bool:
        for tag, quantity in inventory._tags.items():
            if not self.remove_tag(tag, quantity):
                return False
        return True

    def get_all_tags(self) -> list[tuple[str, int]]:
        return list(self._tags.items())


@dataclass
class TagCollection:
    _inventories: dict[TagType, Inventory] = field(default_factory=dict)

    def get_inventory(self, tag_type: TagType) -> Inventory:
        inventory = self._inventories.get(tag_type)
        if inventory is None:
            inventory = Inventory()
            self._inventories[tag_type] = inventory
        return inventory

    def get_quantity(self, tag_type: TagType, tag: str) -> int:
        return self.get_inventory(tag_type).get_quantity(tag)

    def add_tag(self, tag_type: TagType, tag: str, quantity: int):
        inventory = self.get_inventory(tag_type)
        inventory.add_tag(tag, quantity)

    def remove_tag(self, tag_type: TagType, tag: str, quantity: int) -> bool:
        inventory = self.get_inventory(tag_type)
        return inventory.remove_tag(tag, quantity)

    def add_inventory(self, tag_type: TagType, inventory: Inventory):
        current_inventory = self.get_inventory(tag_type)
        current_inventory.add_inventory(inventory)

    def remove_inventory(self, tag_type: TagType, inventory: Inventory) -> bool:
        current_inventory = self.get_inventory(tag_type)
        return current_inventory.remove_inventory(inventory)

    def add_tag_collection(self, other: "TagCollection"):
        for tag_type, inventory in other._inventories.items():
            self.add_inventory(tag_type, inventory)

    def remove_tag_collection(self, other: "TagCollection") -> bool:
        for tag_type, inventory in other._inventories.items():
            if not self.remove_inventory(tag_type, inventory):
                return False
        return True

    def get_all_tags(self) -> list[tuple[TagType, str, int]]:
        return [
            (tag_type, tag, quantity)
            for tag_type, inventory in self._inventories.items()
            for tag, quantity in inventory.get_all_tags()
        ]
