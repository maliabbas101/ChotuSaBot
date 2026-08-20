"""Structured logging setup. No print() anywhere else in the bot."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


class _StructuredFormatter(logging.Formatter):
    """Compact single-line format: timestamp level logger: message."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging(log_level: str = "INFO", log_file: Path | None = None) -> None:
    """Configure the root logger once at startup.

    Logs to stdout always, and additionally to `log_file` if provided.
    Safe to call multiple times (handlers are not duplicated).
    """
    root = logging.getLogger()
    root.setLevel(log_level.upper())

    if root.handlers:
        # Already configured (e.g. re-imported in tests) — don't duplicate.
        return

    formatter = _StructuredFormatter()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    # discord.py's own logger is noisy at DEBUG; keep it at INFO unless the
    # whole app is explicitly set to DEBUG.
    if log_level.upper() != "DEBUG":
        logging.getLogger("discord").setLevel(logging.WARNING)
