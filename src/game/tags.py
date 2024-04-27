from dataclasses import dataclass, field
from enum import Enum


class TagType(Enum):
    ITEM = "item"


@dataclass
class Inventory:
    tags: dict[str, int] = field(default_factory=dict)

    def add_tag(self, tag: str, quantity: int):
        if quantity <= 0:
            return
        if tag not in self.tags:
            self.tags[tag] = quantity
            return
        self.tags[tag] += quantity

    def remove_tag(self, tag: str, quantity: int) -> bool:
        if quantity <= 0:
            return True
        if tag not in self.tags:
            return False
        current_quantity = self.tags[tag]
        if current_quantity < quantity:
            return False
        self.tags[tag] = current_quantity - quantity
        return True

    def add_inventory(self, inventory: "Inventory"):
        for tag, quantity in inventory.tags.items():
            self.add_tag(tag, quantity)

    def remove_inventory(self, inventory: "Inventory") -> bool:
        for tag, quantity in inventory.tags.items():
            if not self.remove_tag(tag, quantity):
                return False
        return True


@dataclass
class TagCollection:
    tags: dict[TagType, Inventory] = field(default_factory=dict)

    def get_inventory(self, tag_type: TagType) -> Inventory:
        inventory = self.tags.get(tag_type)
        if inventory is None:
            inventory = Inventory()
            self.tags[tag_type] = inventory
        return inventory

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
        for tag_type, inventory in other.tags.items():
            self.add_inventory(tag_type, inventory)

    def remove_tag_collection(self, other: "TagCollection") -> bool:
        for tag_type, inventory in other.tags.items():
            if not self.remove_inventory(tag_type, inventory):
                return False
        return True
