from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord

import channel_automation
import server_config as cfg
from data_store import JsonDataStore


def _text_channel(category_name=None, name="general", channel_id=1):
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = channel_id
    channel.name = name
    channel.category = SimpleNamespace(name=category_name) if category_name else None
    channel.send = AsyncMock()
    return channel


def _message(channel, content="", attachments=None, author_bot=False, author_name="Ali"):
    author = MagicMock()
    author.bot = author_bot
    author.display_name = author_name
    message = MagicMock(spec=discord.Message)
    message.channel = channel
    message.content = content
    message.attachments = attachments or []
    message.embeds = []
    message.author = author
    message.create_thread = AsyncMock()
    return message


def _attachment(content_type):
    return SimpleNamespace(content_type=content_type, filename="pic.png")


async def test_image_post_in_media_category_creates_thread(tmp_path):
    store = JsonDataStore(tmp_path / "data.json")
    await store.load()

    channel = _text_channel(category_name=cfg.MEDIA_CATEGORY_NAME, name="artnclicks")
    message = _message(channel, attachments=[_attachment("image/png")], author_name="Ali")

    await channel_automation.handle_message_automation(store, message)

    message.create_thread.assert_called_once()
    _, kwargs = message.create_thread.call_args
    assert kwargs["name"] == "Ali post"


async def test_text_only_post_in_media_category_does_not_create_thread(tmp_path):
    store = JsonDataStore(tmp_path / "data.json")
    await store.load()

    channel = _text_channel(category_name=cfg.MEDIA_CATEGORY_NAME, name="artnclicks")
    message = _message(channel, content="no picture here")

    await channel_automation.handle_message_automation(store, message)

    message.create_thread.assert_not_called()


async def test_image_post_outside_media_category_does_not_create_thread(tmp_path):
    store = JsonDataStore(tmp_path / "data.json")
    await store.load()

    channel = _text_channel(category_name="General", name="general")
    message = _message(channel, attachments=[_attachment("image/png")])

    await channel_automation.handle_message_automation(store, message)

    message.create_thread.assert_not_called()


async def test_confessions_channel_creates_discussion_thread(tmp_path):
    store = JsonDataStore(tmp_path / "data.json")
    await store.load()

    channel = _text_channel(name=cfg.CONFESSIONS_CHANNEL)
    message = _message(channel, content="a confession")

    await channel_automation.handle_message_automation(store, message)

    message.create_thread.assert_called_once()


async def test_intro_channel_creates_welcome_thread_and_reposts_sticky(tmp_path):
    store = JsonDataStore(tmp_path / "data.json")
    await store.load()

    channel = _text_channel(name=cfg.INTRO_CHANNEL)
    sticky_message = MagicMock()
    sticky_message.id = 999
    channel.send.return_value = sticky_message
    message = _message(channel, content="hi im new here", author_name="NewUser")

    await channel_automation.handle_message_automation(store, message)

    message.create_thread.assert_called_once()
    channel.send.assert_called_once_with(cfg.STICKY_INTRO_MESSAGE)
    sticky = await store.get("sticky_messages", {})
    assert sticky[str(channel.id)] == 999


async def test_bot_authored_messages_are_ignored(tmp_path):
    store = JsonDataStore(tmp_path / "data.json")
    await store.load()

    channel = _text_channel(name=cfg.CONFESSIONS_CHANNEL)
    message = _message(channel, content="a confession", author_bot=True)

    await channel_automation.handle_message_automation(store, message)

    message.create_thread.assert_not_called()
