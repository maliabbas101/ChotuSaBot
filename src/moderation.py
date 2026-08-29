"""Moderation: /purge and image-only-channel enforcement."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Callable

import discord
from discord import app_commands
from discord.ext import commands

import server_config as cfg

logger = logging.getLogger(__name__)

_MESSAGE_LINK_RE = re.compile(
    r"https?://(?:ptb\.|canary\.)?discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
)

_URL_RE = re.compile(r"https?://\S+")

IMAGE_CONTENT_TYPES = ("image/",)


def _is_image_attachment(attachment: discord.Attachment) -> bool:
    if attachment.content_type and attachment.content_type.startswith(IMAGE_CONTENT_TYPES):
        return True
    return attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))


def message_has_image(message: discord.Message) -> bool:
    if any(_is_image_attachment(a) for a in message.attachments):
        return True
    return any(e.type in ("image", "gifv") for e in message.embeds)


def _filter_all(message: discord.Message) -> bool:
    return True


def _filter_text(message: discord.Message) -> bool:
    return bool(message.content) and not message.attachments and not message.embeds


def _filter_images(message: discord.Message) -> bool:
    return message_has_image(message)


def _filter_attachments(message: discord.Message) -> bool:
    return bool(message.attachments)


def _filter_links(message: discord.Message) -> bool:
    return bool(_URL_RE.search(message.content or ""))


PURGE_FILTERS: dict[str, Callable[[discord.Message], bool]] = {
    "all": _filter_all,
    "text": _filter_text,
    "images": _filter_images,
    "voice/attachments": _filter_attachments,
    "links": _filter_links,
}


def parse_message_link(link: str) -> tuple[int, int, int] | None:
    """Return (guild_id, channel_id, message_id) or None if not a valid link."""
    match = _MESSAGE_LINK_RE.match(link.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def setup_moderation_commands(bot: commands.Bot) -> None:
    @bot.tree.command(name="purge", description="Bulk-delete recent messages")
    @app_commands.describe(
        amount="How many recent messages to scan (max 100)",
        filter="Only delete messages matching this type",
        before_message_link="Optional: only delete messages older than this message (paste link)",
    )
    @app_commands.choices(
        filter=[
            app_commands.Choice(name="All", value="all"),
            app_commands.Choice(name="Text", value="text"),
            app_commands.Choice(name="Images", value="images"),
            app_commands.Choice(name="Voice/Attachments", value="voice/attachments"),
            app_commands.Choice(name="Links", value="links"),
        ]
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge_command(
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100],
        filter: app_commands.Choice[str] | None = None,
        before_message_link: str | None = None,
    ) -> None:
        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            await interaction.response.send_message(
                "This command only works in text channels.", ephemeral=True
            )
            return

        predicate = PURGE_FILTERS[filter.value if filter else "all"]

        before_obj = None
        if before_message_link:
            parsed = parse_message_link(before_message_link)
            if parsed is None:
                await interaction.response.send_message(
                    "That doesn't look like a valid message link.", ephemeral=True
                )
                return
            _, link_channel_id, message_id = parsed
            if link_channel_id != channel.id:
                await interaction.response.send_message(
                    "That message link points to a different channel than this one.",
                    ephemeral=True,
                )
                return
            before_obj = discord.Object(id=message_id)

        await interaction.response.defer(ephemeral=True, thinking=True)
        deleted = await channel.purge(limit=amount, check=predicate, before=before_obj)
        await interaction.followup.send(f"Deleted {len(deleted)} message(s).", ephemeral=True)

    @purge_command.error
    async def purge_command_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You need the Manage Messages permission to use this.", ephemeral=True
            )
            return
        logger.exception("Error in /purge", exc_info=error)
        if interaction.response.is_done():
            await interaction.followup.send("Something went wrong running /purge.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "Something went wrong running /purge.", ephemeral=True
            )


def is_media_channel(channel: discord.abc.GuildChannel) -> bool:
    """True for text channels sitting under the configured media category.

    Deliberately category-based rather than a hardcoded channel name list —
    any channel moved into (or created under) that category picks up the
    image-only behavior automatically. A discord.Thread's `.category` is
    always None (threads aren't direct category children), so replies inside
    the auto-created discussion threads are naturally exempt from this check.
    """
    category = getattr(channel, "category", None)
    return category is not None and category.name == cfg.MEDIA_CATEGORY_NAME


async def enforce_image_only_channel(message: discord.Message) -> bool:
    """Delete `message` if it's in a media-category channel and isn't an image.

    Returns True if the message was deleted (so callers can skip further
    processing of it), False otherwise.
    """
    channel = message.channel
    if not isinstance(channel, discord.TextChannel):
        return False
    if not is_media_channel(channel):
        return False
    if message.author.bot:
        return False
    if message_has_image(message):
        return False

    try:
        await message.delete()
    except discord.HTTPException:
        logger.warning("Failed to delete non-image message in #%s", channel.name)
        return True

    asyncio.create_task(_send_transient_notice(channel, message.author))
    return True


async def _send_transient_notice(channel: discord.TextChannel, author: discord.abc.User) -> None:
    try:
        notice = await channel.send(
            f"{author.mention} this channel is images only — text posts get removed. "
            "Feel free to chat about it in another channel!"
        )
        await asyncio.sleep(7)
        await notice.delete()
    except discord.HTTPException:
        pass
