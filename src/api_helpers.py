"""Gemini REST calls: chat replies, persona-aware prompting, summarization.

Plain aiohttp POSTs to the Generative Language API — no SDK, to keep the
process footprint small. Every call goes through retry_async for transient
5xx/timeout errors, and rotates to the next configured API key immediately
on HTTP 429 (rate limit) before giving up — the single biggest reliability
win for a free-tier key.
"""

from __future__ import annotations

import logging

import aiohttp

from retry_utils import RETRYABLE_HTTP_STATUS, RetryableError, retry_async

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
REQUEST_TIMEOUT_SECONDS = 20


class GeminiAPIError(Exception):
    """Non-retryable failure from the Gemini API (bad request, blocked, etc.)."""


class GeminiRateLimitError(Exception):
    """HTTP 429 — caller should rotate to the next API key."""


class GeminiClient:
    def __init__(self, api_keys: list[str], model: str, session: aiohttp.ClientSession) -> None:
        self._api_keys = api_keys
        self._model = model
        self._session = session

    @property
    def enabled(self) -> bool:
        return len(self._api_keys) > 0

    async def generate(
        self,
        contents: list[dict],
        system_instruction: str | None = None,
        temperature: float = 0.9,
        max_output_tokens: int = 300,
    ) -> str | None:
        """Generate text, rotating across configured keys on rate limit.

        Returns None if AI is disabled, all keys are exhausted/rate-limited,
        or the response was empty (e.g. blocked by Gemini's own safety filter).
        """
        if not self._api_keys:
            return None

        for index, key in enumerate(self._api_keys):
            try:
                return await retry_async(
                    self._post_once,
                    contents,
                    system_instruction,
                    temperature,
                    max_output_tokens,
                    key,
                    retries=1,
                    retry_exceptions=(RetryableError, aiohttp.ClientError),
                )
            except GeminiRateLimitError:
                logger.info("Gemini key #%d rate-limited, rotating to next key", index + 1)
                continue
            except GeminiAPIError as exc:
                logger.warning("Gemini API error, not retrying: %s", exc)
                return None
            except Exception as exc:  # noqa: BLE001 - never let AI failures crash the bot
                logger.warning("Gemini call failed: %s", exc)
                return None

        logger.warning("All %d Gemini key(s) exhausted or rate-limited", len(self._api_keys))
        return None

    async def _post_once(
        self,
        contents: list[dict],
        system_instruction: str | None,
        temperature: float,
        max_output_tokens: int,
        api_key: str,
    ) -> str | None:
        url = f"{GEMINI_BASE_URL}/{self._model}:generateContent?key={api_key}"
        payload: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        async with self._session.post(url, json=payload, timeout=timeout) as resp:
            if resp.status == 429:
                raise GeminiRateLimitError("Gemini returned 429")
            if resp.status in RETRYABLE_HTTP_STATUS:
                raise RetryableError(f"Gemini returned {resp.status}")
            if resp.status != 200:
                body = await resp.text()
                raise GeminiAPIError(f"Gemini returned {resp.status}: {body[:200]}")

            data = await resp.json()

        try:
            candidate = data["candidates"][0]
            parts = candidate["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip() or None
        except (KeyError, IndexError, TypeError):
            logger.info("Gemini response had no usable text (likely safety-blocked)")
            return None


def build_text_content(role: str, text: str) -> dict:
    return {"role": role, "parts": [{"text": text}]}
