"""Utility features that don't need AI: /vctime and /adopt.

(/stats lives in main_bot.py since it was the first end-to-end command;
/tldr lives in api_helpers.py-backed ai_chat.py since it requires Gemini.)
"""

from __future__ import annotations

import datetime as dt
import logging

import discord
from discord import app_commands
from discord.ext import commands

from data_store import JsonDataStore

logger = logging.getLogger(__name__)

# --- Voice-channel time tracking --------------------------------------------
# In-memory only: {user_id: joined_at}. Lost on restart — acceptable, since a
# restart mid-session just means that one partial session isn't counted.
_voice_join_times: dict[int, dt.datetime] = {}


async def _add_vc_seconds(store: JsonDataStore, user_id: int, seconds: float) -> None:
    if seconds <= 0:
        return

    def mutate(section: dict) -> None:
        section[str(user_id)] = section.get(str(user_id), 0) + seconds

    await store.update_section("vc_time", mutate)


async def handle_voice_state_update(
    store: JsonDataStore,
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState,
) -> None:
    now = discord.utils.utcnow()
    if before.channel is None and after.channel is not None:
        _voice_join_times[member.id] = now
    elif before.channel is not None and after.channel is None:
        start = _voice_join_times.pop(member.id, None)
        if start is not None:
            await _add_vc_seconds(store, member.id, (now - start).total_seconds())


def _format_duration(seconds: float) -> str:
    total_minutes = int(seconds // 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


# --- Virtual pet -------------------------------------------------------------
DECAY_PER_HOUR = 2.0  # hunger rises / happiness falls by this much per hour idle


def _apply_decay(pet: dict) -> dict:
    now = dt.datetime.now(dt.timezone.utc)
    last = dt.datetime.fromisoformat(pet["last_interaction"])
    hours = max(0.0, (now - last).total_seconds() / 3600)
    pet["hunger"] = min(100, pet["hunger"] + hours * DECAY_PER_HOUR)
    pet["happiness"] = max(0, pet["happiness"] - hours * DECAY_PER_HOUR)
    pet["last_interaction"] = now.isoformat()
    return pet


def _pet_embed(owner_name: str, pet: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"{pet['name']} ({owner_name}'s pet)", color=discord.Color.magenta()
    )
    embed.add_field(name="Hunger", value=f"{int(pet['hunger'])}/100", inline=True)
    embed.add_field(name="Happiness", value=f"{int(pet['happiness'])}/100", inline=True)
    return embed


def setup_utility_commands(bot: commands.Bot) -> None:
    @bot.tree.command(name="vctime", description="Show voice-channel time")
    @app_commands.describe(user="Whose time to show (defaults to you)")
    async def vctime_command(
        interaction: discord.Interaction, user: discord.Member | None = None
    ) -> None:
        target = user or interaction.user
        vc_time: dict = await bot.store.get("vc_time", {})  # type: ignore[attr-defined]
        seconds = vc_time.get(str(target.id), 0)

        join_time = _voice_join_times.get(target.id)
        if join_time is not None:
            seconds += (discord.utils.utcnow() - join_time).total_seconds()

        duration = _format_duration(seconds)
        await interaction.response.send_message(
            f"**{target.display_name}** has spent **{duration}** in voice channels."
        )

    adopt_group = app_commands.Group(name="adopt", description="Virtual pet")

    @adopt_group.command(name="new", description="Adopt a new pet")
    @app_commands.describe(name="Your pet's name")
    async def adopt_new(interaction: discord.Interaction, name: str) -> None:
        pets: dict = await bot.store.get("pet_system", {})  # type: ignore[attr-defined]
        if str(interaction.user.id) in pets:
            await interaction.response.send_message(
                f"You already have a pet named **{pets[str(interaction.user.id)]['name']}**!",
                ephemeral=True,
            )
            return

        pet = {
            "name": name[:32],
            "hunger": 50,
            "happiness": 50,
            "last_interaction": dt.datetime.now(dt.timezone.utc).isoformat(),
        }

        def mutate(section: dict) -> None:
            section[str(interaction.user.id)] = pet

        await bot.store.update_section("pet_system", mutate)  # type: ignore[attr-defined]
        await interaction.response.send_message(
            f"You adopted **{pet['name']}**! Use `/adopt feed` and `/adopt play` to take care."
        )

    @adopt_group.command(name="feed", description="Feed your pet")
    async def adopt_feed(interaction: discord.Interaction) -> None:
        await _pet_interaction(bot, interaction, hunger_delta=-25, happiness_delta=0, verb="fed")

    @adopt_group.command(name="play", description="Play with your pet")
    async def adopt_play(interaction: discord.Interaction) -> None:
        await _pet_interaction(
            bot, interaction, hunger_delta=0, happiness_delta=20, verb="played with"
        )

    @adopt_group.command(name="status", description="Check on your pet")
    async def adopt_status(interaction: discord.Interaction) -> None:
        pets: dict = await bot.store.get("pet_system", {})  # type: ignore[attr-defined]
        pet = pets.get(str(interaction.user.id))
        if pet is None:
            await interaction.response.send_message(
                "You don't have a pet yet — use `/adopt new` first!", ephemeral=True
            )
            return

        pet = _apply_decay(pet)

        def mutate(section: dict) -> None:
            section[str(interaction.user.id)] = pet

        await bot.store.update_section("pet_system", mutate)  # type: ignore[attr-defined]
        await interaction.response.send_message(
            embed=_pet_embed(interaction.user.display_name, pet)
        )

    bot.tree.add_command(adopt_group)


async def _pet_interaction(
    bot: commands.Bot,
    interaction: discord.Interaction,
    hunger_delta: int,
    happiness_delta: int,
    verb: str,
) -> None:
    pets: dict = await bot.store.get("pet_system", {})  # type: ignore[attr-defined]
    pet = pets.get(str(interaction.user.id))
    if pet is None:
        await interaction.response.send_message(
            "You don't have a pet yet — use `/adopt new` first!", ephemeral=True
        )
        return

    pet = _apply_decay(pet)
    pet["hunger"] = max(0, min(100, pet["hunger"] + hunger_delta))
    pet["happiness"] = max(0, min(100, pet["happiness"] + happiness_delta))

    def mutate(section: dict) -> None:
        section[str(interaction.user.id)] = pet

    await bot.store.update_section("pet_system", mutate)  # type: ignore[attr-defined]
    await interaction.response.send_message(
        f"You {verb} **{pet['name']}**!", embed=_pet_embed(interaction.user.display_name, pet)
    )
