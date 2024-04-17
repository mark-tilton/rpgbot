# This example requires the 'message_content' intent.

import asyncio
from math import floor
import time
import discord
import json
from discord import app_commands
from discord.ext import commands
from datatypes import Activity, ActivityType
from activities import update_activity, start_activity
from items import Item
from storagemodel import StorageModel

guild_id = 1229078590713364602

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
bot = commands.Bot(command_prefix='/', intents=intents)

model = StorageModel()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await tree.sync(guild=discord.Object(id=guild_id))

    general_channel = None
    for channel in client.get_all_channels():
        if channel.type == discord.ChannelType.text:
            if channel.name == "general":
                general_channel = channel
    for user in client.users:
        print(f"{user.name=} {user.id=}")

@tree.command(
    name="chop",
    description="Start chopping trees in this area",
    guild=discord.Object(id=guild_id)
)
async def chop(interaction: discord.Interaction):
    channel = interaction.channel
    user = interaction.user
    name = user.nick or user.display_name
    await interaction.response.send_message(f"{name} is chopping trees in this area.")
    start_activity(model, user.id, ActivityType.WOODCUTTING)

@tree.command(
    name="mine",
    description="Start mining in this area",
    guild=discord.Object(id=guild_id)
)
async def mine(interaction: discord.Interaction):
    channel = interaction.channel
    user = interaction.user
    name = user.nick
    await interaction.response.send_message(f"{name} is mining in {channel.name}")
    start_activity(model, user.id, ActivityType.MINING)

@tree.command(
    name="inventory",
    description="View the items in your inventory",
    guild=discord.Object(id=guild_id)
)
async def inventory(interaction: discord.Interaction):
    user = interaction.user
    update_activity(model, user.id)

    items = model.get_player_items(user.id)
    item_list = "\n".join([f"    {quantity} {item}" for item, quantity in items.items()])
    response_string = f"Inventory: \n{item_list}"

    await interaction.response.send_message(response_string, ephemeral=True)


connection_strings = None
with open("connection_strings.json", mode="r") as f:
    connection_strings = json.load(f)

if not connection_strings:
    print("Failed to parse connection strings file")

client.run(connection_strings["token"])
