"""ChotuSaBot entrypoint: event handlers and slash commands."""

from __future__ import annotations

import logging

import aiohttp
import discord
from discord.ext import commands

import ai_chat
import api_helpers
import channel_automation
from config import Settings, load_settings
from data_store import JsonDataStore
import entertainment
import join_leave
from logging_config import setup_logging
import moderation
import role_panels
import server_config as cfg
import utilities

logger = logging.getLogger(__name__)

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True
INTENTS.voice_states = True
INTENTS.presences = True


class ChotuBot(commands.Bot):
    """Bot subclass holding shared state: settings, data store, invite cache."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(command_prefix="!", intents=INTENTS, help_command=None)
        self.settings = settings
        self.store = JsonDataStore(settings.bot_data_file)
        # guild_id -> {invite_code: uses}; populated on_ready / on_invite_create.
        self.invite_cache: dict[int, dict[str, int]] = {}
        self.http_session: aiohttp.ClientSession | None = None
        self.gemini_client: api_helpers.GeminiClient | None = None

    async def setup_hook(self) -> None:
        await self.store.load()
        logger.info("Data store loaded from %s", self.settings.bot_data_file)

        for view in role_panels.all_persistent_views():
            self.add_view(view)
        logger.info("Registered persistent role-panel views")

        self.http_session = aiohttp.ClientSession()
        self.gemini_client = api_helpers.GeminiClient(
            self.settings.gemini_api_keys, self.settings.gemini_model, self.http_session
        )
        ai_chat.start_dead_chat_task(self, self.gemini_client)

        synced = await self.tree.sync()
        logger.info("Synced %d slash command(s)", len(synced))

    async def close(self) -> None:
        if self.http_session is not None:
            await self.http_session.close()
        await super().close()


bot = ChotuBot(load_settings())
moderation.setup_moderation_commands(bot)
entertainment.setup_entertainment_commands(bot)
utilities.setup_utility_commands(bot)
ai_chat.setup_ai_commands(bot)


@bot.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
) -> None:
    await utilities.handle_voice_state_update(bot.store, member, before, after)


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return

    deleted = await moderation.enforce_image_only_channel(message)
    if deleted:
        return

    await channel_automation.handle_message_automation(bot.store, message)
    await entertainment.check_timed_question_answer(bot.store, message)

    if not message.author.bot:
        ai_chat.record_channel_activity(message.channel.id)
        await ai_chat.update_user_profile(bot.store, message)
        if bot.gemini_client is not None:
            await ai_chat.handle_ambient_reply(bot, bot.gemini_client, message)


@bot.tree.command(name="stats", description="Show server statistics")
async def stats_command(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This command only works inside a server.", ephemeral=True
        )
        return

    online_count = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    role_count = len(guild.roles)
    server_age_days = (discord.utils.utcnow() - guild.created_at).days

    embed = discord.Embed(
        title=f"{guild.name} Stats",
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow(),
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Members", value=str(guild.member_count), inline=True)
    embed.add_field(name="Online", value=str(online_count), inline=True)
    embed.add_field(name="Roles", value=str(role_count), inline=True)
    embed.add_field(
        name="Channels",
        value=f"{text_channels} text / {voice_channels} voice",
        inline=True,
    )
    embed.add_field(name="Server age", value=f"{server_age_days} days", inline=True)
    embed.set_footer(text=cfg.BOT_NAME)

    await interaction.response.send_message(embed=embed)


@bot.event
async def on_ready() -> None:
    logger.info(
        "%s is online as %s (id=%s), in %d guild(s)",
        cfg.BOT_NAME,
        bot.user,
        bot.user.id if bot.user else "?",
        len(bot.guilds),
    )

    for guild in bot.guilds:
        bot.invite_cache[guild.id] = await join_leave.cache_guild_invites(guild)
    logger.info("Cached invites for %d guild(s)", len(bot.invite_cache))


@bot.event
async def on_invite_create(invite: discord.Invite) -> None:
    if invite.guild is None:
        return
    guild_cache = bot.invite_cache.setdefault(invite.guild.id, {})
    guild_cache[invite.code] = invite.uses or 0


@bot.event
async def on_invite_delete(invite: discord.Invite) -> None:
    if invite.guild is None:
        return
    bot.invite_cache.get(invite.guild.id, {}).pop(invite.code, None)


@bot.event
async def on_member_join(member: discord.Member) -> None:
    guild = member.guild
    log_channel = join_leave.get_log_channel(guild)

    cached_uses = bot.invite_cache.get(guild.id, {})
    _invite, label = await join_leave.resolve_used_invite(guild, cached_uses)
    bot.invite_cache[guild.id] = await join_leave.cache_guild_invites(guild)

    if log_channel is not None:
        embed = join_leave.build_join_embed(member, label, guild.member_count)
        await log_channel.send(embed=embed)


@bot.event
async def on_member_remove(member: discord.Member) -> None:
    log_channel = join_leave.get_log_channel(member.guild)
    if log_channel is not None:
        embed = join_leave.build_leave_embed(member, member.guild.member_count)
        await log_channel.send(embed=embed)


def main() -> None:
    settings = bot.settings
    setup_logging(settings.log_level, settings.log_file)
    if not settings.ai_enabled:
        logger.warning(
            "No Gemini API keys configured — AI chat replies and /tldr are disabled. "
            "Moderation, roles, and entertainment commands still work."
        )
    bot.run(settings.discord_token.get_secret_value(), log_handler=None)


if __name__ == "__main__":
    main()
