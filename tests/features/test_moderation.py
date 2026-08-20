from types import SimpleNamespace

import moderation


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
