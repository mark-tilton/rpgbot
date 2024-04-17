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

    TIN_AXE = 13
    COPPER_AXE = 14
    BRONZE_AXE = 15
    IRON_AXE = 16
    STEEL_AXE = 17
    TITANIUM_AXE = 18

ITEM_NAME = {
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

    Item.TIN_AXE: "Tin Axe",
    Item.COPPER_AXE: "Copper Axe",
    Item.BRONZE_AXE: "Bronze Axe",
    Item.IRON_AXE: "Iron Axe",
    Item.STEEL_AXE: "Steel Axe",
    Item.TITANIUM_AXE: "Titanium Axe",
}

ITEM_NAME_REVERSE = {name: item for item, name in ITEM_NAME.items()}

# TODO Item value should rise / fall based on deficit / surplus in the market
ITEM_VALUE = {
    Item.TEAK_LOG: 10,
    Item.WALNUT_LOG: 30,
    Item.PINE_LOG: 40,
    Item.BIRCH_LOG: 70,
    Item.OAK_LOG: 90,
    Item.MAPLE_LOG: 115,
    Item.MAHOGANY_LOG: 145,

    Item.LEAD_ORE: 45,
    Item.TIN_ORE: 75,
    Item.COPPER_ORE: 90,
    Item.IRON_ORE: 100,
    Item.TITANIUM_ORE: 130,

    Item.TIN_AXE: 2000,
    Item.COPPER_AXE: 7000,
    Item.BRONZE_AXE: 23000,
    Item.IRON_AXE: 120000,
    Item.STEEL_AXE: 560000,
    Item.TITANIUM_AXE: 1000000,
}