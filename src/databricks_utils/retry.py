"""Retry/backoff decorator for transient failures (e.g. flaky cloud API or I/O calls)."""

from __future__ import annotations

import functools
import logging
import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


def retry(
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    jitter: float = 0.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry a function on failure with exponential backoff.

    Args:
        max_attempts: total number of attempts before giving up (must be >= 1).
        base_delay: delay in seconds before the first retry.
        backoff_factor: multiplier applied to the delay after each failed attempt.
        exceptions: exception types that should trigger a retry.
        jitter: max random seconds added to each delay, to avoid thundering-herd retries.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            delay = base_delay
            last_exc: BaseException | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        break
                    sleep_for = delay + (random.uniform(0, jitter) if jitter else 0)
                    logger.warning(
                        "%s failed (attempt %d/%d): %s; retrying in %.2fs",
                        func.__qualname__,
                        attempt,
                        max_attempts,
                        exc,
                        sleep_for,
                    )
                    time.sleep(sleep_for)
                    delay *= backoff_factor
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator
