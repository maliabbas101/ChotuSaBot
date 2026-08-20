"""Smoke test: the bot module must import and register all slash commands
without ever connecting to Discord (no live token, no network calls).
"""

EXPECTED_TOP_LEVEL_COMMANDS = {
    "stats",
    "purge",
    "trivia",
    "triviascores",
    "riddle",
    "wyr",
    "qotd",
    "roast",
    "compliment",
    "pomodoro",
    "rekhta",
    "vctime",
    "adopt",
    "tldr",
}


def test_main_bot_imports_and_constructs():
    import main_bot

    assert main_bot.bot is not None
    assert main_bot.bot.user is None  # never logged in


def test_all_expected_slash_commands_are_registered():
    import main_bot

    registered = {c.name for c in main_bot.bot.tree.get_commands()}
    assert registered == EXPECTED_TOP_LEVEL_COMMANDS


def test_adopt_group_has_expected_subcommands():
    import main_bot

    adopt_group = next(c for c in main_bot.bot.tree.get_commands() if c.name == "adopt")
    subcommands = {c.name for c in adopt_group.commands}
    assert subcommands == {"new", "feed", "play", "status"}


def test_bot_intents_enable_message_content_members_voice_and_presences():
    import main_bot

    intents = main_bot.bot.intents
    assert intents.message_content is True
    assert intents.members is True
    assert intents.voice_states is True
    assert intents.presences is True


def test_ai_disabled_without_gemini_keys_but_bot_still_works():
    import main_bot

    assert main_bot.bot.settings.ai_enabled is False
    # Command registration must not depend on AI being configured.
    assert len(main_bot.bot.tree.get_commands()) == len(EXPECTED_TOP_LEVEL_COMMANDS)
