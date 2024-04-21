# This example requires the 'message_content' intent.

from typing import List, Mapping
import discord
import json
from discord.app_commands import CommandTree
from game.game import Game
from game.items import ITEMS
from game.adventure import AdventureReport
from game.zones import ZONES, ZONES_BY_NAME, Zone

guild_id = 1229078590713364602

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = CommandTree(client)

game = Game()

channel_to_zone: Mapping[int, Zone] = {}
zone_to_channel: Mapping[int, int] = {}


@client.event
async def on_ready():
    print("Initializing Zones")
    # Find existing zones
    guild = client.get_guild(guild_id)
    if guild is None or guild.self_role is None:
        raise Exception("Invalid Guild")
    found_zones: set[int] = set()
    for channel in guild.channels:
        zone = ZONES_BY_NAME.get(channel.name, None)
        if zone is not None:
            channel_to_zone[channel.id] = zone
            zone_to_channel[zone.zone_id] = channel.id
            found_zones.add(zone.zone_id)
    
    # Clear out all channels
    for zone_id in found_zones:
        channel_id = zone_to_channel[zone_id]
        channel = guild.get_channel(channel_id)
        if channel is None or not isinstance(channel, discord.TextChannel):
            continue
        await channel.delete()
    found_zones.clear()
        
    # Add new zones to the server
    self_overwrite = discord.PermissionOverwrite()
    self_overwrite.view_channel = True
    self_overwrite.manage_channels = True
    for zone in ZONES:
        if zone.zone_id in found_zones:
            continue
        hidden_overwrite = discord.PermissionOverwrite()
        hidden_overwrite.view_channel = zone.public
        channel = await guild.create_text_channel(
            zone.name,
            overwrites={
                guild.roles[0]: hidden_overwrite,
                guild.self_role: self_overwrite,
            }
        )
        channel_to_zone[channel.id] = zone
        zone_to_channel[zone.zone_id] = channel.id

    print(f'We have logged in as {client.user}')
    await tree.sync(guild=discord.Object(id=guild_id))


async def handle_adventure_report(
        interaction: discord.Interaction,
        report: AdventureReport):
    # Grant access to channels
    shown_overwrite = discord.PermissionOverwrite()
    shown_overwrite.view_channel = True
    guild = interaction.guild
    if guild is None:
        return
    user = interaction.user
    if not isinstance(user, discord.Member):
        return
    for adventure_step in report.adventure_steps:
        for zone_id in adventure_step.zones_discovered:
            channel_id = zone_to_channel[zone_id]
            channel = guild.get_channel(channel_id)
            if not isinstance(channel, discord.TextChannel):
                continue
            await channel.set_permissions(user, overwrite=shown_overwrite)
    
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        return
    await send_adventure_report(channel, report)
            
    
async def send_adventure_report(
        channel: discord.TextChannel,
        report: AdventureReport):
    # Send report
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
        if len(message) == 0:
            continue
        await channel.send("\n".join(message))


@tree.command(
    name="adventure",
    description="Start adventuring in this area.",
    guild=discord.Object(id=guild_id)
)
async def adventure(interaction: discord.Interaction):
    user = interaction.user
    name = user.display_name
    channel = interaction.channel
    if channel is None:
        return
    zone = channel_to_zone[channel.id]

    report = game.start_adventure(user.id, zone.zone_id)
    await interaction.response.send_message(
        f"{name} is adventuring in this area.")

    if report is not None:
        await handle_adventure_report(interaction, report)


@tree.command(
    name="inventory",
    description="View the items in your inventory",
    guild=discord.Object(id=guild_id)
)
async def inventory(interaction: discord.Interaction):
    user = interaction.user

    report = game.update_adventure(user.id)

    items = game.get_player_items(user.id)
    item_list = "\n".join(
        [f"    {quantity}x {ITEMS[item].name}"
            for item, quantity
            in items.items.items()])
    response_string = f"Inventory: \n{item_list}"
    await interaction.response.send_message(response_string, ephemeral=True)

    if report is not None:
        await handle_adventure_report(interaction, report)


@tree.command(
    name="give",
    description="Give yourself an item",
    guild=discord.Object(id=guild_id)
)
async def give(interaction: discord.Interaction, item_id: int, quantity: int):
    user = interaction.user

    with game.storage_model as t:
        t.add_remove_item(user.id, item_id, quantity)
    await interaction.response.send_message(
        f"{user.display_name} is cheating! " +
        f"They gave themself {quantity} {ITEMS[item_id].name}")

connection_strings = None
with open("connection_strings.json", mode="r") as f:
    connection_strings = json.load(f)

if not connection_strings:
    print("Failed to parse connection strings file")

client.run(connection_strings["token"])
