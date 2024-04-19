# This example requires the 'message_content' intent.

import asyncio
import discord
import json
from discord.app_commands import CommandTree, choices, describe, Choice
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
    messages = []
    current_message = ""
    for step in report.adventure_steps:
        step_display = step.display()
        if len(current_message) + len(step_display) > 2000:
            messages.append(current_message)
            current_message = step_display
            continue
        current_message += "\n" + step_display
    messages.append(current_message)
    for message in messages:
        await channel.send(message)

@tree.command(
    name="adventure",
    description="Start adventuring in this area.",
    guild=discord.Object(id=guild_id)
)
async def adventure(interaction: discord.Interaction):
    user = interaction.user
    name = user.display_name
    report = game.start_adventure(user.id, 0)
    if report is not None:
        await send_adventure_report(interaction.channel, report)
    await interaction.response.send_message(f"{name} is adventuring in this area.")

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

    if report is not None:
        await send_adventure_report(interaction.channel, report)

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
