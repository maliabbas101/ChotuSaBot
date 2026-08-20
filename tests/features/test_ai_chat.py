import ai_chat


def test_strip_bot_mention_removes_plain_mention():
    assert ai_chat.strip_bot_mention("<@12345> hey what's up", 12345) == "hey what's up"


def test_strip_bot_mention_removes_nickname_mention():
    assert ai_chat.strip_bot_mention("<@!12345> yo", 12345) == "yo"


def test_strip_bot_mention_leaves_other_mentions_untouched():
    text = "<@99999> did you see this"
    assert ai_chat.strip_bot_mention(text, 12345) == text


def test_profile_hint_empty_for_no_profile():
    assert ai_chat._profile_hint(None) == ""
    assert ai_chat._profile_hint({"recent_messages": []}) == ""


def test_profile_hint_includes_recent_messages():
    profile = {"recent_messages": ["hello", "chai time", "lol"]}
    hint = ai_chat._profile_hint(profile)
    assert "hello" in hint
    assert "chai time" in hint
    assert "lol" in hint


def test_profile_hint_caps_at_five_most_recent():
    profile = {"recent_messages": [str(i) for i in range(10)]}
    hint = ai_chat._profile_hint(profile)
    assert "0" not in hint.split(":")[1]  # oldest entries dropped
    assert "9" in hint
