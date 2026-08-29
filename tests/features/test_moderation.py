from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord

import moderation
import server_config as cfg


def _message(content="", attachments=None, embeds=None):
    return SimpleNamespace(content=content, attachments=attachments or [], embeds=embeds or [])


def _attachment(content_type=None, filename="file.txt"):
    return SimpleNamespace(content_type=content_type, filename=filename)


def _embed(type_="rich"):
    return SimpleNamespace(type=type_)


def test_message_has_image_true_for_image_content_type():
    msg = _message(attachments=[_attachment(content_type="image/png", filename="pic.png")])
    assert moderation.message_has_image(msg)


def test_message_has_image_true_for_image_extension_fallback():
    msg = _message(attachments=[_attachment(content_type=None, filename="pic.JPG")])
    assert moderation.message_has_image(msg)


def test_message_has_image_true_for_image_embed():
    msg = _message(embeds=[_embed("image")])
    assert moderation.message_has_image(msg)


def test_message_has_image_false_for_plain_text():
    msg = _message(content="just chatting")
    assert not moderation.message_has_image(msg)


def test_message_has_image_false_for_non_image_attachment():
    msg = _message(attachments=[_attachment(content_type="application/pdf", filename="doc.pdf")])
    assert not moderation.message_has_image(msg)


def test_filter_text_matches_plain_text_only():
    plain = _message(content="hello there")
    with_attachment = _message(content="hello", attachments=[_attachment("image/png", "a.png")])
    assert moderation.PURGE_FILTERS["text"](plain)
    assert not moderation.PURGE_FILTERS["text"](with_attachment)


def test_filter_images_matches_only_images():
    img = _message(attachments=[_attachment("image/png", "a.png")])
    pdf = _message(attachments=[_attachment("application/pdf", "a.pdf")])
    assert moderation.PURGE_FILTERS["images"](img)
    assert not moderation.PURGE_FILTERS["images"](pdf)


def test_filter_attachments_matches_any_attachment():
    voice_note = _message(attachments=[_attachment("audio/ogg", "voice-message.ogg")])
    assert moderation.PURGE_FILTERS["voice/attachments"](voice_note)
    assert not moderation.PURGE_FILTERS["voice/attachments"](_message(content="text only"))


def test_filter_links_detects_urls():
    with_link = _message(content="check this out https://example.com/page")
    without_link = _message(content="no links here")
    assert moderation.PURGE_FILTERS["links"](with_link)
    assert not moderation.PURGE_FILTERS["links"](without_link)


def test_filter_all_matches_everything():
    assert moderation.PURGE_FILTERS["all"](_message(content="anything"))
    assert moderation.PURGE_FILTERS["all"](_message())


def test_parse_message_link_valid():
    link = "https://discord.com/channels/111/222/333"
    assert moderation.parse_message_link(link) == (111, 222, 333)


def test_parse_message_link_handles_canary_and_ptb_subdomains():
    assert moderation.parse_message_link("https://canary.discord.com/channels/1/2/3") == (1, 2, 3)
    assert moderation.parse_message_link("https://ptb.discord.com/channels/1/2/3") == (1, 2, 3)


def test_parse_message_link_invalid_returns_none():
    assert moderation.parse_message_link("not a link") is None
    assert moderation.parse_message_link("https://example.com/nope") is None


def _text_channel(category_name=None, name="general"):
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = name
    channel.category = SimpleNamespace(name=category_name) if category_name else None
    return channel


def test_is_media_channel_true_when_category_matches():
    channel = _text_channel(category_name=cfg.MEDIA_CATEGORY_NAME)
    assert moderation.is_media_channel(channel)


def test_is_media_channel_false_when_category_differs():
    channel = _text_channel(category_name="General")
    assert not moderation.is_media_channel(channel)


def test_is_media_channel_false_when_no_category():
    channel = _text_channel(category_name=None)
    assert not moderation.is_media_channel(channel)


def test_is_media_channel_false_for_thread_without_category_attr():
    thread = SimpleNamespace()  # discord.Thread has no `.category`
    assert not moderation.is_media_channel(thread)


async def _mock_message(channel, content="", attachments=None, embeds=None, author_bot=False):
    author = MagicMock()
    author.bot = author_bot
    author.mention = "@someone"
    message = MagicMock(spec=discord.Message)
    message.channel = channel
    message.content = content
    message.attachments = attachments or []
    message.embeds = embeds or []
    message.author = author
    message.delete = AsyncMock()
    return message


async def test_enforce_image_only_channel_deletes_text_only_post():
    channel = _text_channel(category_name=cfg.MEDIA_CATEGORY_NAME)
    channel.send = AsyncMock()
    message = await _mock_message(channel, content="just chatting, no picture")

    deleted = await moderation.enforce_image_only_channel(message)

    assert deleted is True
    message.delete.assert_called_once()


async def test_enforce_image_only_channel_allows_image_post():
    channel = _text_channel(category_name=cfg.MEDIA_CATEGORY_NAME)
    message = await _mock_message(channel, attachments=[_attachment("image/png", "pic.png")])

    deleted = await moderation.enforce_image_only_channel(message)

    assert deleted is False
    message.delete.assert_not_called()


async def test_enforce_image_only_channel_ignores_channels_outside_media_category():
    channel = _text_channel(category_name="General")
    message = await _mock_message(channel, content="text is fine here")

    deleted = await moderation.enforce_image_only_channel(message)

    assert deleted is False
    message.delete.assert_not_called()


async def test_enforce_image_only_channel_ignores_bot_authors():
    channel = _text_channel(category_name=cfg.MEDIA_CATEGORY_NAME)
    message = await _mock_message(channel, content="bot text", author_bot=True)

    deleted = await moderation.enforce_image_only_channel(message)

    assert deleted is False
    message.delete.assert_not_called()
