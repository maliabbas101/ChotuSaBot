"""Typed application configuration loaded from environment / .env file."""

from __future__ import annotations

from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, populated from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Required ---------------------------------------------------------
    discord_token: SecretStr

    # --- Storage ------------------------------------------------------------
    bot_data_file: Path = Path("data/bot_data.json")

    # --- Gemini (AI features) ----------------------------------------------
    # Multiple keys support automatic rotation on HTTP 429 (rate limit).
    gemini_api_key_1: SecretStr | None = None
    gemini_api_key_2: SecretStr | None = None
    gemini_api_key_3: SecretStr | None = None
    gemini_api_key_4: SecretStr | None = None
    gemini_model: str = "gemini-3.6-flash"

    # --- Optional external content API --------------------------------------
    api_ninjas_key: SecretStr | None = None

    # --- Logging ------------------------------------------------------------
    log_level: str = "INFO"
    log_file: Path | None = None

    @field_validator("log_file", mode="before")
    @classmethod
    def _blank_log_file_is_unset(cls, value: object) -> object:
        # An empty LOG_FILE= in .env would otherwise become Path(""), which
        # resolves to the current directory and crashes logging_config's
        # FileHandler trying to open a directory as a file.
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def gemini_api_keys(self) -> list[str]:
        """Non-empty Gemini keys in rotation order."""
        keys = [
            self.gemini_api_key_1,
            self.gemini_api_key_2,
            self.gemini_api_key_3,
            self.gemini_api_key_4,
        ]
        return [k.get_secret_value() for k in keys if k is not None and k.get_secret_value()]

    @property
    def ai_enabled(self) -> bool:
        """AI features are disabled (not a hard crash) when no key is configured."""
        return len(self.gemini_api_keys) > 0


def load_settings() -> Settings:
    """Load settings, failing fast and loudly if required values are missing."""
    try:
        return Settings()  # type: ignore[call-arg]
    except Exception as exc:  # pydantic ValidationError
        raise SystemExit(
            "Failed to load configuration. Check your .env file against "
            f".env.example.\n\nDetails: {exc}"
        ) from exc
