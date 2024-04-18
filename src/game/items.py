from typing import List
import yaml
from dataclasses import dataclass

@dataclass
class Item:
    item_id: int
    name: str
    plural: str

def load_items() -> List[Item]:
    with open("data/items.yaml", mode="r") as f:
        item_list_yaml = yaml.safe_load(f)
    items = []
    for item_yaml in item_list_yaml:
        item_id = item_yaml["item"]
        name = item_yaml["name"].lower()
        plural = item_yaml.get("plural", name + "s").lower()
        item = Item(item_id, name, plural)
        items.append(item)
    items.sort(key=lambda step: step.item_id)
    return items

def build_format_dictionary(items: List[Item]) -> dict[str, str]:
    plural_options = ["s", "p"]
    casing_options = ["l", "c", "t"]
    item_format_dict = {}
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