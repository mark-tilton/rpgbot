from collections.abc import Mapping
from dataclasses import dataclass, field

import yaml


@dataclass
class Item:
    item_id: str
    name: str
    plural: str


@dataclass
class Inventory:
    items: dict[str, int] = field(default_factory=dict)

    def add_item(self, item_id: str, quantity: int):
        if quantity <= 0:
            return
        if item_id not in self.items:
            self.items[item_id] = quantity
            return
        self.items[item_id] += quantity

    def remove_item(self, item_id: str, quantity: int) -> bool:
        if quantity <= 0:
            return True
        if item_id not in self.items:
            return False
        current_quantity = self.items[item_id]
        if current_quantity < quantity:
            return False
        self.items[item_id] = current_quantity - quantity
        return True

    def add_inventory(self, inventory: "Inventory"):
        for item_id, quantity in inventory.items.items():
            self.add_item(item_id, quantity)

    def remove_inventory(self, inventory: "Inventory") -> bool:
        for item_id, quantity in inventory.items.items():
            if not self.remove_item(item_id, quantity):
                return False
        return True


def load_items() -> Mapping[str, Item]:
    with open("data/items.yaml", mode="r") as f:
        item_list_yaml = yaml.safe_load(f)
    items: dict[str, Item] = {}
    for item_yaml in item_list_yaml:
        item_id: str = item_yaml["item"]
        name: str = item_yaml.get("name", item_id.replace("_", " ")).lower()
        plural: str = item_yaml.get("plural", name + "s").lower()
        item = Item(item_id, name, plural)
        if item_id in items:
            raise Exception(f"Duplicate item id found: {item_id}")
        items[item_id] = item
    return items


ITEMS = load_items()
