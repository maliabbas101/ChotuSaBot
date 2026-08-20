"""Shared bootstrap for the one-time role-panel setup scripts.

Each setup_*_roles.py script logs in a minimal client, finds the requested
channel by name, sends the panel message(s) + view, then exits — panels are
posted once, not recreated on every bot restart (main_bot.py re-registers
the persistent views on startup so the buttons keep working).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import discord

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import load_settings  # noqa: E402


def parse_channel_arg(description: str) -> str:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--channel",
        required=True,
        help="Name of the text channel to post the panel into (without '#').",
    )
    return parser.parse_args().channel


async def post_panel(channel_name: str, title: str, body: str, views) -> None:
    """Log in, find `channel_name` in the first guild the bot is in, post."""
    settings = load_settings()
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        try:
            guild = client.guilds[0] if client.guilds else None
            if guild is None:
                print("Bot isn't in any guild yet — invite it first.")
                return

            channel = discord.utils.get(guild.text_channels, name=channel_name)
            if channel is None:
                print(
                    f"Channel '#{channel_name}' not found in {guild.name}. "
                    "Create it first or pass the correct --channel name."
                )
                return

            embed = discord.Embed(title=title, description=body, color=discord.Color.blurple())
            for i, view in enumerate(views):
                if i == 0:
                    await channel.send(embed=embed, view=view)
                else:
                    await channel.send(content=f"{title} (page {i + 1})", view=view)
            print(f"Posted panel to #{channel_name} in {guild.name}.")
        finally:
            await client.close()

    await client.start(settings.discord_token.get_secret_value())
