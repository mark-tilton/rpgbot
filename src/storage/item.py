from enum import Enum

class Item(Enum):
    TEAK_LOG = 1
    WALNUT_LOG = 2
    PINE_LOG = 3
    BIRCH_LOG = 4
    OAK_LOG = 5
    MAPLE_LOG = 6
    MAHOGANY_LOG = 7
    LEAD_ORE = 8
    TIN_ORE = 9
    COPPER_ORE = 10
    IRON_ORE = 11
    TITANIUM_ORE = 12

ITEM_NAMES = {
    Item.TEAK_LOG: "Teak Log",
    Item.WALNUT_LOG: "Walnut Log",
    Item.PINE_LOG: "Pine Log",
    Item.BIRCH_LOG: "Birch Log",
    Item.OAK_LOG: "Oak Log",
    Item.MAPLE_LOG: "Maple Log",
    Item.MAHOGANY_LOG: "Mahogany Log",
    Item.LEAD_ORE: "Lead Ore",
    Item.TIN_ORE: "Tin Ore",
    Item.COPPER_ORE: "Copper Ore",
    Item.IRON_ORE: "Iron Ore",
    Item.TITANIUM_ORE: "Titanium Ore",
}

ITEM_NAME_LOOKUP = {name: item for item, name in ITEM_NAMES.items()}