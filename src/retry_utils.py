"""Generic exponential-backoff retry wrapper for flaky outbound HTTP calls."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)

# HTTP status codes worth retrying: rate limit + transient server errors.
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}


class RetryableError(Exception):
    """Raised by callers to signal a retryable failure that isn't a plain exception."""


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args,
    retries: int = 2,
    delay: float = 0.5,
    backoff: float = 2.0,
    retry_exceptions: tuple[type[BaseException], ...] = (
        RetryableError,
        asyncio.TimeoutError,
        ConnectionError,
    ),
    **kwargs,
) -> T:
    """Call `func(*args, **kwargs)`, retrying on `retry_exceptions` with backoff+jitter.

    Total attempts = retries + 1. Raises the last exception if all attempts fail.
    """
    attempt = 0
    current_delay = delay

    while True:
        try:
            return await func(*args, **kwargs)
        except retry_exceptions as exc:
            attempt += 1
            if attempt > retries:
                logger.warning("retry_async: giving up after %d attempt(s): %s", attempt, exc)
                raise

            jitter = current_delay * random.uniform(0.0, 0.25)
            sleep_for = current_delay + jitter
            logger.info(
                "retry_async: attempt %d/%d failed (%s), retrying in %.2fs",
                attempt,
                retries + 1,
                exc,
                sleep_for,
            )
            await asyncio.sleep(sleep_for)
            current_delay *= backoff
