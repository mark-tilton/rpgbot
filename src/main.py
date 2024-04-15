# This example requires the 'message_content' intent.

import asyncio
import time
import discord
import json
from discord import app_commands
from discord.ext import commands
from datatypes import Activity, ActivityType
from activities import update_activity
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

    model.init_tables()

    general_channel = None
    for channel in client.get_all_channels():
        if channel.type == discord.ChannelType.text:
            if channel.name == "general":
                general_channel = channel
    for user in client.users:
        print(f"{user.name=} {user.id=}")

@tree.command(
    name="mine",
    description="Start mining in this area",
    guild=discord.Object(id=guild_id)
)
async def mine(interaction: discord.Interaction, material: str):
    channel = interaction.channel
    user = interaction.user
    await interaction.response.send_message(f"{user.name} is mining in {channel.name}")
    message_id = (await interaction.original_response()).id
    model.start_activity(user.id, Activity(ActivityType.MINING, int(time.time()), channel.id, message_id))

    message = await channel.fetch_message(message_id)
    for i in range(100):
        await asyncio.sleep(5)
        update_activity(model, user.id)
        await message.edit(content=f"{(i + 1) * 5} {material} mined")
    print("Done")


connection_strings = None
with open("connection_strings.json", mode="r") as f:
    connection_strings = json.load(f)

if not connection_strings:
    print("Failed to parse connection strings file")

client.run(connection_strings["token"])
