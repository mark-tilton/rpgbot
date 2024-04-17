from typing import List
from storage.item import Item


class Vendor:
    def __init__(self, name: str, description: str, items: List[Item]):
        self.name = name
        self.description = description
        self.items = items

HEMLOCK = Vendor(
    "Hemlock",
    description="Logging vendor, buys and sells logs and axes",
    items=[
        Item.TEAK_LOG,
        Item.WALNUT_LOG,
        Item.PINE_LOG,
        Item.BIRCH_LOG,
        Item.OAK_LOG,
        Item.MAPLE_LOG,
        Item.MAHOGANY_LOG,

        Item.TIN_AXE,
        Item.COPPER_AXE,
        Item.BRONZE_AXE,
        Item.IRON_AXE,
        Item.STEEL_AXE,
        Item.TITANIUM_AXE,
    ]
)

VENDORS = [
    HEMLOCK
]

VENDORS_BY_NAME = {vendor.name: vendor for vendor in VENDORS}