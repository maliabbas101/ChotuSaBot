"""Join/leave log embeds + invite-use tracking.

Invite tracking approach: cache guild.invites() uses on startup and whenever
on_invite_create fires, then diff against fresh uses on_member_join to find
which invite code went up. Vanity URLs, expired invites, and invites created
by bump/listing bots don't diff cleanly, so those fall back to a labeled
guess instead of crashing or showing "Unknown".
"""

from __future__ import annotations

import logging

import discord

import server_config as cfg

logger = logging.getLogger(__name__)


async def cache_guild_invites(guild: discord.Guild) -> dict[str, int]:
    """Snapshot {invite_code: uses} for a guild. Empty dict if we lack permission."""
    try:
        invites = await guild.invites()
    except discord.Forbidden:
        logger.warning("Missing permission to fetch invites for guild %s", guild.name)
        return {}
    return {invite.code: invite.uses or 0 for invite in invites}


async def resolve_used_invite(
    guild: discord.Guild, cached_uses: dict[str, int]
) -> tuple[discord.Invite | None, str]:
    """Diff current invite uses against `cached_uses` to find which was used.

    Returns (invite_or_None, label). `invite` is None when we can't identify
    a specific invite (vanity URL, race condition, external bot) — `label`
    is always a sensible, non-crashing description in that case.
    """
    try:
        current_invites = await guild.invites()
    except discord.Forbidden:
        return None, cfg.FALLBACK_INVITE_LABEL

    for invite in current_invites:
        previous_uses = cached_uses.get(invite.code, 0)
        if (invite.uses or 0) > previous_uses:
            inviter = invite.inviter
            if inviter is not None and inviter.bot:
                for needle, label in cfg.KNOWN_EXTERNAL_INVITE_LABELS.items():
                    if needle in inviter.name.lower():
                        return invite, label
            inviter_label = f"invited by {inviter}" if inviter else f"via code {invite.code}"
            return invite, inviter_label

    # No normal invite ticked up — check vanity URL if the guild has one.
    if guild.vanity_url_code:
        try:
            vanity = await guild.vanity_invite()
        except (discord.Forbidden, discord.HTTPException):
            vanity = None
        if vanity is not None:
            previous_uses = cached_uses.get(vanity.code, 0)
            if (vanity.uses or 0) > previous_uses:
                return None, "via server vanity URL"

    return None, cfg.FALLBACK_INVITE_LABEL


def build_join_embed(member: discord.Member, invite_label: str, member_count: int) -> discord.Embed:
    account_age_days = (discord.utils.utcnow() - member.created_at).days
    embed = discord.Embed(
        title="Member joined",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="User", value=f"{member.mention} ({member})", inline=False)
    embed.add_field(name="Invite", value=invite_label, inline=True)
    embed.add_field(name="Account age", value=f"{account_age_days} days", inline=True)
    embed.add_field(name="Member count", value=str(member_count), inline=True)
    return embed


def build_leave_embed(member: discord.Member, member_count: int) -> discord.Embed:
    joined_at = member.joined_at
    joined_str = discord.utils.format_dt(joined_at, style="R") if joined_at else "unknown"
    roles = [r.mention for r in member.roles if r.name != "@everyone"]
    roles_str = ", ".join(roles) if roles else "none"

    embed = discord.Embed(
        title="Member left",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
    embed.add_field(name="Joined", value=joined_str, inline=True)
    embed.add_field(name="Member count", value=str(member_count), inline=True)
    embed.add_field(name="Roles", value=roles_str, inline=False)
    return embed


def get_log_channel(guild: discord.Guild) -> discord.TextChannel | None:
    channel = discord.utils.get(guild.text_channels, name=cfg.LOG_CHANNEL)
    if channel is None:
        logger.warning(
            "Log channel #%s not found in %s — join/leave logs won't be posted.",
            cfg.LOG_CHANNEL,
            guild.name,
        )
    return channel
