"""Entertainment slash commands backed by the static question_bank content."""

from __future__ import annotations

import asyncio
import dataclasses
import logging
import random

import discord
from discord import app_commands
from discord.ext import commands

import question_bank as qb
import server_config as cfg
from data_store import JsonDataStore

logger = logging.getLogger(__name__)

TRIVIA_TIMEOUT_SECONDS = 120
RIDDLE_TIMEOUT_SECONDS = 300


@dataclasses.dataclass
class ActiveQuestion:
    accepted_answers: set[str]
    display_answer: str
    kind: str  # "trivia" | "riddle"


# One active timed question per channel at a time, keyed by channel id.
_active_questions: dict[int, ActiveQuestion] = {}


async def _increment_trivia_score(store: JsonDataStore, user_id: int, display_name: str) -> None:
    def mutate(scores: dict) -> None:
        entry = scores.setdefault(str(user_id), {"name": display_name, "score": 0})
        entry["name"] = display_name
        entry["score"] += 1

    await store.update_section("trivia_scores", mutate)


async def _expire_question(
    channel: discord.abc.Messageable, channel_id: int, question: ActiveQuestion, delay: int
) -> None:
    await asyncio.sleep(delay)
    if _active_questions.get(channel_id) is question:
        _active_questions.pop(channel_id, None)
        await channel.send(f"Time's up! The answer was **{question.display_answer}**.")


async def check_timed_question_answer(store: JsonDataStore, message: discord.Message) -> None:
    """Call from on_message: checks a guess against any active trivia/riddle."""
    if message.author.bot:
        return
    active = _active_questions.get(message.channel.id)
    if active is None:
        return
    guess = message.content.strip().lower()
    if guess not in active.accepted_answers:
        return

    _active_questions.pop(message.channel.id, None)
    await message.channel.send(
        f"{message.author.mention} got it! The answer was **{active.display_answer}**."
    )
    if active.kind == "trivia":
        await _increment_trivia_score(store, message.author.id, message.author.display_name)


def setup_entertainment_commands(bot: commands.Bot) -> None:
    @bot.tree.command(name="trivia", description="Answer a trivia question (2 minutes)")
    async def trivia_command(interaction: discord.Interaction) -> None:
        channel = interaction.channel
        if channel is None:
            return
        if channel.id in _active_questions:
            await interaction.response.send_message(
                "There's already an active question in this channel.", ephemeral=True
            )
            return

        item = random.choice(qb.TRIVIA_QUESTIONS)
        question = ActiveQuestion(
            accepted_answers=set(item["answers"]),
            display_answer=item["answers"][0],
            kind="trivia",
        )
        _active_questions[channel.id] = question

        embed = discord.Embed(
            title=f"Trivia — {item['category']}",
            description=item["question"],
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"You have {TRIVIA_TIMEOUT_SECONDS // 60} minutes to answer!")
        await interaction.response.send_message(embed=embed)

        asyncio.create_task(_expire_question(channel, channel.id, question, TRIVIA_TIMEOUT_SECONDS))

    @bot.tree.command(name="triviascores", description="Show the trivia leaderboard")
    async def triviascores_command(interaction: discord.Interaction) -> None:
        scores: dict = await bot.store.get("trivia_scores", {})  # type: ignore[attr-defined]
        if not scores:
            await interaction.response.send_message("No trivia answers recorded yet.")
            return

        ranked = sorted(scores.values(), key=lambda e: e["score"], reverse=True)[:10]
        lines = [f"{i + 1}. **{e['name']}** — {e['score']}" for i, e in enumerate(ranked)]
        embed = discord.Embed(
            title="Trivia Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="riddle", description="Answer a riddle (5 minutes)")
    async def riddle_command(interaction: discord.Interaction) -> None:
        channel = interaction.channel
        if channel is None:
            return
        if channel.id in _active_questions:
            await interaction.response.send_message(
                "There's already an active question in this channel.", ephemeral=True
            )
            return

        item = random.choice(qb.RIDDLES)
        question = ActiveQuestion(
            accepted_answers=set(item["answers"]),
            display_answer=item["answers"][0],
            kind="riddle",
        )
        _active_questions[channel.id] = question

        embed = discord.Embed(
            title="Riddle",
            description=item["riddle"],
            color=discord.Color.purple(),
        )
        embed.set_footer(text=f"You have {RIDDLE_TIMEOUT_SECONDS // 60} minutes to answer!")
        await interaction.response.send_message(embed=embed)

        asyncio.create_task(_expire_question(channel, channel.id, question, RIDDLE_TIMEOUT_SECONDS))

    @bot.tree.command(name="wyr", description="Get a Would You Rather prompt")
    async def wyr_command(interaction: discord.Interaction) -> None:
        prompt = random.choice(qb.WOULD_YOU_RATHER)
        embed = discord.Embed(
            title="Would You Rather", description=prompt, color=discord.Color.teal()
        )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="qotd", description="Get the question of the day")
    async def qotd_command(interaction: discord.Interaction) -> None:
        prompt = random.choice(qb.QOTD_PROMPTS)
        embed = discord.Embed(
            title="Question of the Day", description=prompt, color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="roast", description="Friendly roast for a member")
    @app_commands.describe(user="Who to roast")
    async def roast_command(interaction: discord.Interaction, user: discord.Member) -> None:
        template = random.choice(qb.ROAST_TEMPLATES)
        await interaction.response.send_message(template.format(user=user.mention))

    @bot.tree.command(name="compliment", description="Compliment a member")
    @app_commands.describe(user="Who to compliment")
    async def compliment_command(interaction: discord.Interaction, user: discord.Member) -> None:
        template = random.choice(qb.COMPLIMENT_TEMPLATES)
        await interaction.response.send_message(template.format(user=user.mention))

    @bot.tree.command(name="pomodoro", description="Start a study timer")
    @app_commands.describe(minutes="Timer length in minutes (max 60)")
    async def pomodoro_command(
        interaction: discord.Interaction, minutes: app_commands.Range[int, 1, 60]
    ) -> None:
        await interaction.response.send_message(
            f"⏳ Pomodoro started for **{minutes} minute(s)**. I'll ping you when time's up!"
        )
        user = interaction.user
        channel = interaction.channel
        asyncio.create_task(_run_pomodoro(user, channel, minutes))

    if cfg.ENABLE_REKHTA_COMMAND:

        @bot.tree.command(name="rekhta", description="Get a random Urdu poetry couplet")
        async def rekhta_command(interaction: discord.Interaction) -> None:
            item = random.choice(qb.REKHTA_COUPLETS)
            embed = discord.Embed(description=item["couplet"], color=discord.Color.dark_gold())
            embed.set_footer(text=f"— {item['poet']}")
            await interaction.response.send_message(embed=embed)


async def _run_pomodoro(
    user: discord.abc.User, channel: discord.abc.Messageable | None, minutes: int
) -> None:
    await asyncio.sleep(minutes * 60)
    message = f"⏰ {user.mention} your {minutes}-minute pomodoro is up! Time for a break."
    try:
        await user.send(message)
    except discord.HTTPException:
        if channel is not None:
            await channel.send(message)
