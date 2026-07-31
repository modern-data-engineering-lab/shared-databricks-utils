from __future__ import annotations

import pytest

from databricks_utils.retry import retry


def test_retry_returns_result_on_first_success() -> None:
    calls = []

    @retry(max_attempts=3, base_delay=0)
    def succeed() -> str:
        calls.append(1)
        return "ok"

    assert succeed() == "ok"
    assert len(calls) == 1


def test_retry_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("time.sleep", lambda _: None)
    calls = []

    @retry(max_attempts=3, base_delay=0.01, exceptions=(ValueError,))
    def flaky() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("not yet")
        return "ok"

    assert flaky() == "ok"
    assert len(calls) == 3


def test_retry_raises_after_exhausting_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("time.sleep", lambda _: None)
    calls = []

    @retry(max_attempts=3, base_delay=0.01, exceptions=(ValueError,))
    def always_fails() -> None:
        calls.append(1)
        raise ValueError("nope")

    with pytest.raises(ValueError, match="nope"):
        always_fails()
    assert len(calls) == 3


def test_retry_does_not_catch_unlisted_exceptions() -> None:
    calls = []

    @retry(max_attempts=3, base_delay=0, exceptions=(ValueError,))
    def wrong_error() -> None:
        calls.append(1)
        raise TypeError("boom")

    with pytest.raises(TypeError, match="boom"):
        wrong_error()
    assert len(calls) == 1


def test_retry_applies_exponential_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", sleeps.append)

    @retry(max_attempts=4, base_delay=1.0, backoff_factor=2.0, exceptions=(ValueError,))
    def always_fails() -> None:
        raise ValueError("nope")

    with pytest.raises(ValueError):
        always_fails()

    assert sleeps == [1.0, 2.0, 4.0]


def test_retry_rejects_invalid_max_attempts() -> None:
    with pytest.raises(ValueError, match="max_attempts"):

        @retry(max_attempts=0)
        def noop() -> None:
            pass
