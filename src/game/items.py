from dataclasses import dataclass, field

import yaml


@dataclass
class Item:
    item_id: int
    name: str
    plural: str


@dataclass
class Inventory:
    items: dict[int, int] = field(default_factory=dict)

    def add_item(self, item_id: int, quantity: int):
        if quantity <= 0:
            return
        if item_id not in self.items:
            self.items[item_id] = quantity
            return
        self.items[item_id] += quantity

    def remove_item(self, item_id: int, quantity: int) -> bool:
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


def load_items() -> list[Item]:
    with open("data/items.yaml", mode="r") as f:
        item_list_yaml = yaml.safe_load(f)
    items: list[Item] = []
    for item_yaml in item_list_yaml:
        item_id = item_yaml["item"]
        name = item_yaml["name"].lower()
        plural = item_yaml.get("plural", name + "s").lower()
        item = Item(item_id, name, plural)
        items.append(item)
    items.sort(key=lambda step: step.item_id)
    return items


def build_format_dictionary(items: list[Item]) -> dict[str, str]:
    plural_options = ["s", "p"]
    casing_options = ["l", "c", "t"]
    item_format_dict: dict[str, str] = {}
    for item in items:
        for plural in plural_options:
            for casing in casing_options:
                key = f"i{item.item_id}{plural}{casing}"
                value = item.name if plural == "s" else item.plural
                if casing == "l":
                    value = value.lower()
                elif casing == "c":
                    value = value.capitalize()
                elif casing == "t":
                    value = value.title()
                item_format_dict[key] = value
    return item_format_dict


ITEMS = load_items()
ITEM_FORMAT_DICT = build_format_dictionary(ITEMS)
