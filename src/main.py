# This example requires the 'message_content' intent.

from typing import List
import discord
import json
from discord.app_commands import CommandTree
from game.game import Game
from game.items import ITEMS
from game.adventure import AdventureReport

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

async def send_adventure_report(channel: discord.TextChannel, report: AdventureReport):
    messages: List[List[str]] = []
    report_lines = report.display().splitlines()
    current_message = []
    message_length = 0
    for line in report_lines:
        line_length = len(line) + 2
        if line_length + message_length > 1800:
            messages.append(current_message)
            current_message = [line]
            message_length = line_length
            continue
        current_message.append(line)
        message_length += line_length
    messages.append(current_message)
    for message in messages:
        await channel.send("\n".join(message))

@tree.command(
    name="adventure",
    description="Start adventuring in this area.",
    guild=discord.Object(id=guild_id)
)
async def adventure(interaction: discord.Interaction):
    user = interaction.user
    name = user.display_name
    report = game.start_adventure(user.id, 0)
    channel = interaction.channel
    await interaction.response.send_message(f"{name} is adventuring in this area.")
    if report is not None and channel is not None and isinstance(channel, discord.TextChannel):
        await send_adventure_report(channel, report)

@tree.command(
    name="inventory",
    description="View the items in your inventory",
    guild=discord.Object(id=guild_id)
)
async def inventory(interaction: discord.Interaction):
    user = interaction.user

    report = game.update_adventure(user.id)

    items = game.get_player_items(user.id)
    item_list = "\n".join([f"    {quantity}x {ITEMS[item].name}" for item, quantity in items.items.items()])
    response_string = f"Inventory: \n{item_list}"
    await interaction.response.send_message(response_string, ephemeral=True)

    channel = interaction.channel
    if report is not None and channel is not None and isinstance(channel, discord.TextChannel):
        await send_adventure_report(channel, report)

@tree.command(
    name="give",
    description="Give yourself an item",
    guild=discord.Object(id=guild_id)
)
async def give(interaction: discord.Interaction, item_id: int, quantity: int):
    user = interaction.user

    with game.storage_model as t:
        t.add_remove_item(user.id, item_id, quantity)
    await interaction.response.send_message(f"{user.display_name} is cheating! They gave themself {quantity} {ITEMS[item_id].name}")

connection_strings = None
with open("connection_strings.json", mode="r") as f:
    connection_strings = json.load(f)

if not connection_strings:
    print("Failed to parse connection strings file")

client.run(connection_strings["token"])
