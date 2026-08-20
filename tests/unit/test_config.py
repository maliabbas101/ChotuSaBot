from pathlib import Path

import pytest

from config import Settings


def test_missing_discord_token_fails_fast(monkeypatch):
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    with pytest.raises(Exception):
        Settings(_env_file=None)


def test_ai_disabled_when_no_gemini_keys():
    settings = Settings(_env_file=None, discord_token="x")
    assert settings.ai_enabled is False
    assert settings.gemini_api_keys == []


def test_ai_enabled_when_at_least_one_gemini_key_present():
    settings = Settings(_env_file=None, discord_token="x", gemini_api_key_2="secret-key")
    assert settings.ai_enabled is True
    assert settings.gemini_api_keys == ["secret-key"]


def test_gemini_keys_rotation_order_and_blank_filtering():
    settings = Settings(
        _env_file=None,
        discord_token="x",
        gemini_api_key_1="key1",
        gemini_api_key_2="",
        gemini_api_key_3="key3",
    )
    assert settings.gemini_api_keys == ["key1", "key3"]


def test_blank_log_file_env_value_is_treated_as_unset(monkeypatch):
    monkeypatch.setenv("LOG_FILE", "")
    settings = Settings(_env_file=None, discord_token="x")
    assert settings.log_file is None


def test_populated_log_file_env_value_is_kept():
    settings = Settings(_env_file=None, discord_token="x", log_file="logs/bot.log")
    assert settings.log_file == Path("logs/bot.log")
