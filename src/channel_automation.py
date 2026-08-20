"""Auto-threading + sticky intro message for confessions/intro/image channels."""

from __future__ import annotations

import logging

import discord

import server_config as cfg
from data_store import JsonDataStore
from moderation import message_has_image

logger = logging.getLogger(__name__)

THREAD_ARCHIVE_MINUTES = 1440  # 24h


async def _safe_create_thread(message: discord.Message, name: str) -> None:
    try:
        await message.create_thread(name=name[:100], auto_archive_duration=THREAD_ARCHIVE_MINUTES)
    except discord.HTTPException as exc:
        logger.warning("Failed to create thread on message %s: %s", message.id, exc)


async def _repost_sticky_intro(store: JsonDataStore, channel: discord.TextChannel) -> None:
    sticky = await store.get("sticky_messages", {})
    last_id = sticky.get(str(channel.id))

    if last_id is not None:
        try:
            old_message = await channel.fetch_message(last_id)
            await old_message.delete()
        except discord.HTTPException:
            pass  # already gone or inaccessible — fine, we just post a fresh one

    new_message = await channel.send(cfg.STICKY_INTRO_MESSAGE)
    await store.update_section(
        "sticky_messages", lambda section: section.update({str(channel.id): new_message.id})
    )


async def handle_message_automation(store: JsonDataStore, message: discord.Message) -> None:
    """Dispatch confessions/intro/image-channel automation for one message.

    Call this from on_message after the moderation image-only-channel check
    has already run (and only if the message wasn't deleted by it).
    """
    channel = message.channel
    if message.author.bot or not isinstance(channel, discord.TextChannel):
        return

    if channel.name == cfg.CONFESSIONS_CHANNEL:
        await _safe_create_thread(message, "Discuss this confession")
        return

    if channel.name == cfg.INTRO_CHANNEL:
        await _safe_create_thread(message, f"Welcome, {message.author.display_name}!")
        await _repost_sticky_intro(store, channel)
        return

    if channel.name in cfg.IMAGE_ONLY_CHANNELS and message_has_image(message):
        await _safe_create_thread(message, "Comments")
        return
