import json
from collections.abc import Mapping

import discord
from discord.app_commands import CommandTree
from discord.ext import tasks

from game.adventure import AdventureReport
from game.game import Game
from game.items import ITEMS
from game.zones import ZONES, Zone
from game.tags import TagType

guild_id = 1229078590713364602

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = CommandTree(client)

game = Game()

channel_to_zone: Mapping[int, Zone] = {}
zone_to_channel: Mapping[str, int] = {}


@client.event
async def on_ready():
    print("Initializing Zones")
    # Find existing zones
    guild = client.get_guild(guild_id)
    if guild is None or guild.self_role is None:
        raise Exception("Invalid Guild")
    found_zones: set[str] = set()
    for channel in guild.channels:
        zone = ZONES.get(channel.name, None)
        if zone is not None:
            channel_to_zone[channel.id] = zone
            zone_to_channel[zone.zone_id] = channel.id
            found_zones.add(zone.zone_id)

    # Clear out all channels
    # for zone_id in found_zones:
    #     channel_id = zone_to_channel[zone_id]
    #     channel = guild.get_channel(channel_id)
    #     if channel is None or not isinstance(channel, discord.TextChannel):
    #         continue
    #     await channel.delete()
    # found_zones.clear()

    # Add new zones to the server
    self_overwrite = discord.PermissionOverwrite()
    self_overwrite.view_channel = True
    self_overwrite.manage_channels = True
    for zone_id, zone in ZONES.items():
        if zone_id in found_zones:
            continue
        hidden_overwrite = discord.PermissionOverwrite()
        hidden_overwrite.view_channel = zone.public
        channel = await guild.create_text_channel(
            zone_id,
            overwrites={
                guild.roles[0]: hidden_overwrite,
                guild.self_role: self_overwrite,
            },
        )
        channel_to_zone[channel.id] = zone
        zone_to_channel[zone.zone_id] = channel.id

    print(f"We have logged in as {client.user}")
    await tree.sync(guild=discord.Object(id=guild_id))
    update_adventures.start()

def get_interaction_info(interaction: discord.Interaction) -> tuple[discord.Guild, discord.TextChannel, discord.Member]:
    guild = interaction.guild
    if guild is None:
        raise Exception("Invalid guild")
    channel = interaction.channel
    if channel is None or not isinstance(channel, discord.TextChannel):
        raise Exception("Invalid channel")
    user = interaction.user
    if not isinstance(user, discord.Member):
        raise Exception("User is not a member")
    return guild, channel, user


async def handle_adventure_report(
    guild: discord.Guild, channel: discord.TextChannel, user: discord.Member, report: AdventureReport
):
    # Grant access to channels
    shown_overwrite = discord.PermissionOverwrite()
    shown_overwrite.view_channel = True
    for adventure_group in report.adventure_groups:
        for adventure_step in adventure_group.steps:
            for zone_id in adventure_step.get_discovered_zones():
                discovered_channel_id = zone_to_channel[zone_id]
                discovered_channel = guild.get_channel(discovered_channel_id)
                if not isinstance(discovered_channel, discord.TextChannel):
                    continue
                await channel.set_permissions(user, overwrite=shown_overwrite)

    # Send updates to the adventure thread
    await send_adventure_report(channel, user.display_name, report)


async def send_adventure_report(
    channel: discord.TextChannel, user_name: str, report: AdventureReport
):
    # Send report
    thread_id = report.adventure.thread_id
    thread = channel.get_thread(thread_id)
    if not thread:
        raise Exception(f"Thread not found: {thread_id}")
    messages: list[list[str]] = []
    report_lines = report.display().splitlines()
    current_message = []
    message_length = 0
    for line in report_lines:
        line_length = len(line) + 2
        if line_length + message_length > 1000 and line == "":
            messages.append(current_message)
            current_message = ["_ _"]
            message_length = line_length
            continue
        current_message.append(line)
        message_length += line_length
    messages.append(current_message)
    for message in messages:
        if len(message) == 0:
            continue
        await thread.send("\n".join(message))
    # await thread.edit(archived=True)

@tasks.loop(seconds=5)
async def update_adventures():
    for user in client.get_all_members():
        report = game.update_adventure(user.id)
        if report is not None:
            guild = client.get_guild(guild_id)
            if guild is None: 
                print(f"Guild {guild_id} was not found")
                continue
            zone_id = report.adventure.zone_id
            channel_id = zone_to_channel[zone_id]
            channel = guild.get_channel(channel_id)
            if channel is None or not isinstance(channel, discord.TextChannel):
                print(f"Channel {channel_id} was invalid")
                continue
            await handle_adventure_report(guild, channel, user, report)

@tree.command(
    name="adventure",
    description="Start adventuring in this area.",
    guild=discord.Object(id=guild_id),
)
async def adventure(interaction: discord.Interaction):
    guild, channel, user = get_interaction_info(interaction)
    name = user.display_name
    thread = await channel.create_thread(
        name=f"{name}'s adventure report", type=discord.ChannelType.public_thread
    )
    zone = channel_to_zone[channel.id]

    report = game.start_adventure(user.id, zone.zone_id, thread.id)
    await interaction.response.send_message(f"{name} is adventuring in this area.")

    if report is not None:
        await handle_adventure_report(guild, channel, user, report)


@tree.command(
    name="inventory",
    description="View the items in your inventory",
    guild=discord.Object(id=guild_id),
)
async def inventory(interaction: discord.Interaction):
    guild, channel, user = get_interaction_info(interaction)

    report = game.update_adventure(user.id)

    items = game.get_player_tags(user.id).get_inventory(TagType.ITEM).get_all_tags()
    item_list = "\n".join(
        [
            f"    {quantity}x {ITEMS[item].name}"
            for item, quantity in items
        ]
    )
    response_string = f"Inventory: \n{item_list}"
    await interaction.response.send_message(response_string, ephemeral=True)

    if report is not None:
        await handle_adventure_report(guild, channel, user, report)


@tree.command(
    name="give", description="Give yourself an item", guild=discord.Object(id=guild_id)
)
async def give(interaction: discord.Interaction, item_id: str, quantity: int):
    user = interaction.user

    with game.storage_model as t:
        t.add_remove_tag(user.id, TagType.ITEM, item_id, quantity)
    await interaction.response.send_message(
        f"{user.display_name} is cheating! "
        + f"They gave themself {quantity} {ITEMS[item_id].name}"
    )


connection_strings = None
with open("connection_strings.json", mode="r") as f:
    connection_strings = json.load(f)

if not connection_strings:
    print("Failed to parse connection strings file")

client.run(connection_strings["token"])
