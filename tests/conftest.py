import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

# main_bot.py builds the bot object at import time, which requires a token
# to be present. Tests never actually log in, so a dummy value is enough.
os.environ["DISCORD_TOKEN"] = "test-token-for-pytest"

# A real .env file may exist in the repo root with live secrets — since
# pydantic-settings falls back to .env for any var not already set in the
# environment, explicitly blank these out so tests never pick up real
# Gemini/API keys and stay deterministic regardless of local dev setup.
for _optional_var in (
    "GEMINI_API_KEY_1",
    "GEMINI_API_KEY_2",
    "GEMINI_API_KEY_3",
    "GEMINI_API_KEY_4",
    "API_NINJAS_KEY",
    "LOG_FILE",
):
    os.environ[_optional_var] = ""
