"""Async-safe atomic JSON persistence — the bot's only storage layer.

No database: a single JSON file on disk, guarded by an asyncio.Lock so
concurrent event handlers can't interleave writes, with writes done
atomically (temp file + fsync + os.replace) so a crash mid-write can never
corrupt the real file.
"""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default shape — each feature owns one top-level key. New keys are added
# here (and picked up automatically for existing data files via the
# dict.setdefault merge in load()) rather than requiring a migration step.
DEFAULT_DATA: dict[str, Any] = {
    "pet_system": {},
    "vc_time": {},
    "trivia_scores": {},
    "user_profiles": {},
    "sticky_messages": {},
}


class JsonDataStore:
    """Wraps a JSON file on disk with locked, atomic read/write access."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        self._data: dict[str, Any] | None = None

    async def load(self) -> dict[str, Any]:
        """Load the JSON file into memory, creating it with defaults if missing.

        Recovers from a corrupt/truncated file by falling back to defaults
        rather than crashing the bot on startup.
        """
        async with self._lock:
            self._data = await asyncio.to_thread(self._read_or_init)
            return self._data

    def _read_or_init(self) -> dict[str, Any]:
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = copy.deepcopy(DEFAULT_DATA)
            self._write_sync(data)
            return data

        try:
            raw = self._path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("root JSON value is not an object")
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            logger.error(
                "bot_data.json is corrupt or unreadable (%s); "
                "reinitializing with defaults. Original file left in place.",
                exc,
            )
            data = copy.deepcopy(DEFAULT_DATA)
            self._write_sync(data)
            return data

        # Merge in any new top-level keys introduced since this file was
        # last written, without touching existing values.
        changed = False
        for key, default_value in DEFAULT_DATA.items():
            if key not in data:
                data[key] = default_value if not isinstance(default_value, dict) else {}
                changed = True
        if changed:
            self._write_sync(data)
        return data

    def _write_sync(self, data: dict[str, Any]) -> None:
        """Atomic write: temp file in the same dir, fsync, then os.replace()."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self._path.parent), prefix=f".{self._path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self._path)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    async def save(self) -> None:
        """Persist the current in-memory state to disk atomically."""
        if self._data is None:
            raise RuntimeError("load() must be called before save()")
        async with self._lock:
            await asyncio.to_thread(self._write_sync, self._data)

    @property
    def data(self) -> dict[str, Any]:
        """Direct access to the in-memory dict. Mutate freely, then call save()."""
        if self._data is None:
            raise RuntimeError("load() must be called before accessing data")
        return self._data

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self.data.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        """Set a top-level key and persist immediately."""
        async with self._lock:
            self.data[key] = value
            await asyncio.to_thread(self._write_sync, self.data)

    async def update_section(self, key: str, mutate) -> None:
        """Run `mutate(section_dict)` on `data[key]` under the lock, then persist.

        `mutate` should mutate the dict in place (or return a replacement).
        """
        async with self._lock:
            section = self.data.setdefault(key, {})
            result = mutate(section)
            if result is not None:
                self.data[key] = result
            await asyncio.to_thread(self._write_sync, self.data)
