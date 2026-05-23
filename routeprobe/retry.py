"""Retry logic for transient HTTP failures in route probing."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class RetryConfig:
    """Configuration for retry behaviour."""

    max_attempts: int = 3
    backoff_factor: float = 0.5
    retry_on_status: tuple[int, ...] = (429, 500, 502, 503, 504)
    retry_on_exception: tuple[type[BaseException], ...] = (OSError, TimeoutError)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.backoff_factor < 0:
            raise ValueError("backoff_factor must be non-negative")

    def should_retry_status(self, status_code: int) -> bool:
        return status_code in self.retry_on_status

    def delay_for(self, attempt: int) -> float:
        """Return seconds to wait before the given attempt (0-indexed)."""
        if attempt == 0:
            return 0.0
        return self.backoff_factor * (2 ** (attempt - 1))


@dataclass
class RetryStats:
    """Records what happened during a retried call."""

    attempts: int = 0
    delays: list[float] = field(default_factory=list)


def with_retry(
    fn: Callable,
    config: Optional[RetryConfig] = None,
    *,
    _sleep: Callable[[float], None] = time.sleep,
) -> tuple[object, RetryStats]:
    """Call *fn* with retry logic defined by *config*.

    Returns ``(result, stats)`` where *result* is the return value of *fn*
    on success.  Raises the last exception if all attempts are exhausted.
    """
    if config is None:
        config = RetryConfig()

    stats = RetryStats()
    last_exc: Optional[BaseException] = None

    for attempt in range(config.max_attempts):
        delay = config.delay_for(attempt)
        if delay > 0:
            _sleep(delay)
            stats.delays.append(delay)

        stats.attempts += 1
        try:
            result = fn()
        except config.retry_on_exception as exc:
            last_exc = exc
            continue

        # If the callable returned a response-like object, check status.
        status = getattr(result, "status_code", None)
        if status is not None and config.should_retry_status(status):
            last_exc = None  # not an exception path
            if attempt < config.max_attempts - 1:
                continue

        return result, stats

    if last_exc is not None:
        raise last_exc

    # Exhausted retries on bad status — return last result anyway.
    return result, stats  # type: ignore[return-value]
