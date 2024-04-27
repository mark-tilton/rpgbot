from collections.abc import Mapping
from dataclasses import dataclass

import yaml


@dataclass
class Item:
    item_id: str
    name: str
    plural: str


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
