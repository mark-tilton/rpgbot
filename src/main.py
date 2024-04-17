# This example requires the 'message_content' intent.

import discord
import json
from discord.app_commands import CommandTree, choices, describe, Choice
from game.woodcutting import LOG_TYPES
from storage.item import ITEM_NAME, ITEM_NAME_REVERSE, Item
from storage.activity import ActivityType
from game.game import Game

guild_id = 1229078590713364602

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = CommandTree(client)

game = Game()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await tree.sync(guild=discord.Object(id=guild_id))

@tree.command(
    name="chop",
    description="Start woodcutting in this area",
    guild=discord.Object(id=guild_id)
)
@describe(log_id="The type of tree to chop")
@choices(log_id=[Choice(name=ITEM_NAME[log], value=log.value) for log in LOG_TYPES])
async def chop(interaction: discord.Interaction, log_id: int):
    user = interaction.user
    name = user.display_name
    log_type = Item(log_id)
    result = game.start_woodcutting(user_id=user.id, log_type=log_type)
    if not result.valid:
        await interaction.response.send_message(f"Unable to start woodcutting: {result.message}", ephemeral=True)
        return
    await interaction.response.send_message(f"{name} is chopping {ITEM_NAME[log_type]}s in this area.")

@tree.command(
    name="mine",
    description="Start mining in this area",
    guild=discord.Object(id=guild_id)
)
async def mine(interaction: discord.Interaction):
    user = interaction.user
    name = user.display_name
    await interaction.response.send_message(f"{name} is mining in this area.")
    game.start_activity(user.id, ActivityType.MINING)

@tree.command(
    name="inventory",
    description="View the items in your inventory",
    guild=discord.Object(id=guild_id)
)
async def inventory(interaction: discord.Interaction):
    user = interaction.user
    game.update_activity(user.id)

    items = game.get_player_items(user.id)
    item_list = "\n".join([f"    {quantity} {ITEM_NAME[item]}" for item, quantity in items.items()])
    response_string = f"Inventory: \n{item_list}"

    await interaction.response.send_message(response_string, ephemeral=True)

@tree.command(
    name="buy",
    description="Buy an item",
    guild=discord.Object(id=guild_id)
)
async def buy(interaction: discord.Interaction, item_name: str, quantity: int = 1):
    user = interaction.user
    name = user.display_name
    item = ITEM_NAME_REVERSE.get(item_name, None)
    if item is None:
        await interaction.response.send_message(f"{item_name} is not a valid item.", ephemeral=True)
        return
    game.buy_item(user.id, item, quantity)
    await interaction.response.send_message(f"{name} has purchased {quantity} {item_name}{'s' if quantity > 1 else ''}.")

@tree.command(
    name="equip",
    description="Buy an item",
    guild=discord.Object(id=guild_id)
)
async def equip(interaction: discord.Interaction, item_name: str):
    user = interaction.user
    name = user.display_name
    item = ITEM_NAME_REVERSE.get(item_name, None)
    if item is None:
        await interaction.response.send_message(f"{item_name} is not a valid item.", ephemeral=True)
        return
    result = game.equip_item(user.id, item)
    if not result.valid:
        await interaction.response.send_message(f"Unable to equip {item_name}: {result.message}")
        return
    await interaction.response.send_message(f"You have equipped your {item_name}.")

@tree.context_menu(guild=discord.Object(id=guild_id))
async def react(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.send_message('Very cool message!', ephemeral=True)

connection_strings = None
with open("connection_strings.json", mode="r") as f:
    connection_strings = json.load(f)

if not connection_strings:
    print("Failed to parse connection strings file")

client.run(connection_strings["token"])
