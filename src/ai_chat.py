"""AI chat replies, persona profiles, dead-chat revival, and /tldr.

Built and wired last since it's the highest-risk feature — every generated
message passes through safety_filter.is_unsafe_output before it can be
sent, and safety_filter.is_serious_topic suppresses replies entirely during
grief/crisis conversations rather than risk a tone-deaf joke.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import random
import re

import discord
from discord import app_commands
from discord.ext import commands, tasks

import api_helpers
from data_store import JsonDataStore
import safety_filter
import server_config as cfg

logger = logging.getLogger(__name__)

CONTEXT_MESSAGE_COUNT = 12
MAX_PROFILE_MESSAGES = 20

AMBIENT_REPLY_PROBABILITY = 0.04
DEAD_CHAT_CHECK_INTERVAL_MINUTES = 15
DEAD_CHAT_THRESHOLD = dt.timedelta(hours=3)
DEAD_CHAT_COOLDOWN = dt.timedelta(hours=6)
DEAD_CHAT_REVIVAL_PROBABILITY = 0.3

TLDR_TRANSCRIPT_CHAR_CAP = 15000

_last_message_time: dict[int, dt.datetime] = {}
_last_revival_time: dict[int, dt.datetime] = {}


def record_channel_activity(channel_id: int) -> None:
    _last_message_time[channel_id] = discord.utils.utcnow()


def strip_bot_mention(content: str, bot_user_id: int) -> str:
    return re.sub(rf"<@!?{bot_user_id}>", "", content).strip()


async def update_user_profile(store: JsonDataStore, message: discord.Message) -> None:
    def mutate(section: dict) -> None:
        entry = section.setdefault(
            str(message.author.id), {"name": message.author.display_name, "recent_messages": []}
        )
        entry["name"] = message.author.display_name
        if message.content:
            entry["recent_messages"] = (entry["recent_messages"] + [message.content[:200]])[
                -MAX_PROFILE_MESSAGES:
            ]

    await store.update_section("user_profiles", mutate)


def _profile_hint(profile: dict | None) -> str:
    if not profile or not profile.get("recent_messages"):
        return ""
    sample = " | ".join(profile["recent_messages"][-5:])
    return (
        f"This user's recent messages, for tone/style reference only (don't quote them): {sample}"
    )


def _emoji_hint(guild: discord.Guild | None) -> str:
    if guild is None or not guild.emojis:
        return ""
    sample = random.sample(list(guild.emojis), min(5, len(guild.emojis)))
    emoji_list = " ".join(f"<:{e.name}:{e.id}>" for e in sample)
    return f"Server custom emojis you may use naturally if they fit (don't force it): {emoji_list}"


async def _build_transcript(
    channel: discord.TextChannel, bot_user_id: int, limit: int
) -> tuple[str, list[discord.Message]]:
    history = [m async for m in channel.history(limit=limit)]
    history.reverse()

    lines = []
    for m in history:
        if m.author.bot and m.author.id != bot_user_id:
            continue
        text = strip_bot_mention(m.content, bot_user_id)
        if not text:
            continue
        speaker = cfg.BOT_NAME if m.author.id == bot_user_id else m.author.display_name
        lines.append(f"{speaker}: {text}")

    return "\n".join(lines), history


async def handle_ambient_reply(
    bot: commands.Bot, gemini_client: api_helpers.GeminiClient, message: discord.Message
) -> None:
    """Probabilistically reply to `message` in-character, or skip."""
    if message.author.bot or not gemini_client.enabled:
        return
    if not isinstance(message.channel, discord.TextChannel):
        return

    is_mentioned = bot.user in message.mentions if bot.user else False
    is_reply_to_bot = bool(
        message.reference
        and isinstance(message.reference.resolved, discord.Message)
        and bot.user
        and message.reference.resolved.author.id == bot.user.id
    )

    if not (is_mentioned or is_reply_to_bot or random.random() < AMBIENT_REPLY_PROBABILITY):
        return

    transcript, history = await _build_transcript(
        message.channel, bot.user.id, CONTEXT_MESSAGE_COUNT  # type: ignore[union-attr]
    )
    combined_for_check = message.content + "\n" + "\n".join(m.content for m in history)
    if safety_filter.is_serious_topic(combined_for_check):
        logger.info("Suppressing ambient AI reply — serious topic in #%s", message.channel)
        return

    store: JsonDataStore = bot.store  # type: ignore[attr-defined]
    profile = (await store.get("user_profiles", {})).get(str(message.author.id))
    system_instruction = "\n".join(
        filter(
            None,
            [
                cfg.BOT_PERSONA,
                _profile_hint(profile),
                _emoji_hint(message.guild),
                "Reply with just the message text, 1-3 sentences, no speaker-name prefix.",
            ],
        )
    )
    contents = [api_helpers.build_text_content("user", transcript or message.content)]

    reply_text = await gemini_client.generate(
        contents, system_instruction=system_instruction, temperature=0.95, max_output_tokens=150
    )
    if reply_text is None:
        return

    if safety_filter.is_unsafe_output(reply_text):
        logger.warning("Blocked unsafe AI output, regenerating once")
        reply_text = await gemini_client.generate(
            contents, system_instruction=system_instruction, temperature=0.6, max_output_tokens=150
        )
        if reply_text is None or safety_filter.is_unsafe_output(reply_text):
            logger.warning("Regenerated AI output still unsafe/empty — suppressing")
            return

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(1.0, 2.5))
    await message.channel.send(reply_text[:2000])


def start_dead_chat_task(bot: commands.Bot, gemini_client: api_helpers.GeminiClient) -> tasks.Loop:
    @tasks.loop(minutes=DEAD_CHAT_CHECK_INTERVAL_MINUTES)
    async def _dead_chat_loop() -> None:
        if not gemini_client.enabled:
            return
        now = discord.utils.utcnow()

        for guild in bot.guilds:
            me = guild.me
            if me is None:
                continue
            for channel in guild.text_channels:
                last_active = _last_message_time.get(channel.id)
                if last_active is None or now - last_active < DEAD_CHAT_THRESHOLD:
                    continue
                last_revival = _last_revival_time.get(channel.id)
                if last_revival and now - last_revival < DEAD_CHAT_COOLDOWN:
                    continue
                if random.random() > DEAD_CHAT_REVIVAL_PROBABILITY:
                    continue
                if not channel.permissions_for(me).send_messages:
                    continue

                system_instruction = "\n".join(
                    [
                        cfg.BOT_PERSONA,
                        "This channel has been quiet for a while. Post one short, casual "
                        "message to restart conversation — a question or observation. "
                        "No speaker-name prefix.",
                    ]
                )
                contents = [api_helpers.build_text_content("user", "(the chat has gone quiet)")]
                text = await gemini_client.generate(
                    contents,
                    system_instruction=system_instruction,
                    temperature=1.0,
                    max_output_tokens=100,
                )
                if text is None or safety_filter.is_unsafe_output(text):
                    continue

                try:
                    await channel.send(text[:2000])
                    _last_revival_time[channel.id] = now
                    _last_message_time[channel.id] = now
                except discord.HTTPException:
                    logger.warning("Failed to send dead-chat revival in #%s", channel.name)

    @_dead_chat_loop.before_loop
    async def _before() -> None:
        await bot.wait_until_ready()

    _dead_chat_loop.start()
    return _dead_chat_loop


def setup_ai_commands(bot: commands.Bot) -> None:
    """Register AI slash commands at module-load time.

    The Gemini client itself is created later in setup_hook (it needs a live
    aiohttp session), so the command body looks it up on `bot` at call time
    via `bot.gemini_client` rather than capturing it here — that keeps
    /tldr's registration consistent with every other command instead of
    depending on setup_hook having already run.
    """

    @bot.tree.command(name="tldr", description="Summarize the last N messages in this channel")
    @app_commands.describe(count="How many recent messages to summarize (50-500)")
    async def tldr_command(
        interaction: discord.Interaction, count: app_commands.Range[int, 50, 500]
    ) -> None:
        gemini_client = bot.gemini_client  # type: ignore[attr-defined]
        if gemini_client is None or not gemini_client.enabled:
            await interaction.response.send_message(
                "AI features aren't configured on this bot yet — /tldr needs a Gemini API key.",
                ephemeral=True,
            )
            return
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "This command only works in text channels.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)

        bot_user_id = bot.user.id  # type: ignore[union-attr]
        transcript, history = await _build_transcript(channel, bot_user_id, count)
        transcript = transcript[-TLDR_TRANSCRIPT_CHAR_CAP:]

        if not transcript:
            await interaction.followup.send("Not enough recent messages to summarize.")
            return

        system_instruction = (
            "Summarize this Discord conversation as a short TL;DR: 3-6 concise bullet points "
            "covering the main topics, decisions, or running jokes. No preamble."
        )
        contents = [api_helpers.build_text_content("user", transcript)]
        summary = await gemini_client.generate(
            contents, system_instruction=system_instruction, temperature=0.4, max_output_tokens=400
        )
        if summary is None:
            await interaction.followup.send(
                "Couldn't generate a summary right now — try again later."
            )
            return

        embed = discord.Embed(
            title=f"TL;DR — last {len(history)} messages",
            description=summary[:4000],
            color=discord.Color.blurple(),
        )
        await interaction.followup.send(embed=embed)
