import pytest

from retry_utils import RetryableError, retry_async


async def test_succeeds_on_first_try_without_sleeping(monkeypatch):
    calls = []

    async def fast_sleep(_seconds):
        calls.append("slept")

    monkeypatch.setattr("retry_utils.asyncio.sleep", fast_sleep)

    async def always_ok():
        return "ok"

    result = await retry_async(always_ok, retries=2)

    assert result == "ok"
    assert calls == []


async def test_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("retry_utils.asyncio.sleep", _fast_sleep)

    attempts = {"count": 0}

    async def fails_once():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RetryableError("transient")
        return "recovered"

    result = await retry_async(fails_once, retries=2, delay=0.01)

    assert result == "recovered"
    assert attempts["count"] == 2


async def test_raises_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr("retry_utils.asyncio.sleep", _fast_sleep)

    attempts = {"count": 0}

    async def always_fails():
        attempts["count"] += 1
        raise RetryableError("still broken")

    with pytest.raises(RetryableError):
        await retry_async(always_fails, retries=2, delay=0.01)

    # initial attempt + 2 retries = 3 total
    assert attempts["count"] == 3


async def test_non_retryable_exception_propagates_immediately(monkeypatch):
    monkeypatch.setattr("retry_utils.asyncio.sleep", _fast_sleep)

    attempts = {"count": 0}

    async def raises_value_error():
        attempts["count"] += 1
        raise ValueError("not retryable by default")

    with pytest.raises(ValueError):
        await retry_async(raises_value_error, retries=3, delay=0.01)

    assert attempts["count"] == 1


async def _fast_sleep(_seconds):
    return None
