"""Tests for routeprobe.retry."""

from __future__ import annotations

import pytest

from routeprobe.retry import RetryConfig, RetryStats, with_retry


# ---------------------------------------------------------------------------
# RetryConfig
# ---------------------------------------------------------------------------

class TestRetryConfig:
    def test_defaults(self):
        cfg = RetryConfig()
        assert cfg.max_attempts == 3
        assert cfg.backoff_factor == 0.5

    def test_invalid_max_attempts(self):
        with pytest.raises(ValueError, match="max_attempts"):
            RetryConfig(max_attempts=0)

    def test_invalid_backoff_factor(self):
        with pytest.raises(ValueError, match="backoff_factor"):
            RetryConfig(backoff_factor=-1)

    def test_should_retry_status_true(self):
        cfg = RetryConfig()
        assert cfg.should_retry_status(503) is True

    def test_should_retry_status_false(self):
        cfg = RetryConfig()
        assert cfg.should_retry_status(200) is False

    def test_delay_for_first_attempt_is_zero(self):
        cfg = RetryConfig(backoff_factor=1.0)
        assert cfg.delay_for(0) == 0.0

    def test_delay_increases_exponentially(self):
        cfg = RetryConfig(backoff_factor=1.0)
        assert cfg.delay_for(1) == 1.0
        assert cfg.delay_for(2) == 2.0
        assert cfg.delay_for(3) == 4.0


# ---------------------------------------------------------------------------
# with_retry — success paths
# ---------------------------------------------------------------------------

def _fake_sleep(seconds: float) -> None:  # noqa: ARG001
    pass


def test_success_on_first_attempt():
    calls = []

    def fn():
        calls.append(1)
        return "ok"

    result, stats = with_retry(fn, _sleep=_fake_sleep)
    assert result == "ok"
    assert stats.attempts == 1
    assert stats.delays == []


def test_retries_on_exception_then_succeeds():
    responses = [OSError("timeout"), OSError("timeout"), "ok"]

    def fn():
        val = responses.pop(0)
        if isinstance(val, Exception):
            raise val
        return val

    result, stats = with_retry(fn, RetryConfig(max_attempts=3), _sleep=_fake_sleep)
    assert result == "ok"
    assert stats.attempts == 3


def test_retries_on_bad_status_then_succeeds():
    class FakeResp:
        def __init__(self, code):
            self.status_code = code

    responses = [FakeResp(503), FakeResp(200)]

    def fn():
        return responses.pop(0)

    result, stats = with_retry(fn, RetryConfig(max_attempts=3), _sleep=_fake_sleep)
    assert result.status_code == 200
    assert stats.attempts == 2


def test_raises_after_all_attempts_exhausted():
    def fn():
        raise OSError("network down")

    with pytest.raises(OSError, match="network down"):
        with_retry(fn, RetryConfig(max_attempts=3), _sleep=_fake_sleep)


def test_delays_recorded():
    recorded: list[float] = []

    def fake_sleep(s: float) -> None:
        recorded.append(s)

    responses = [OSError(), "ok"]

    def fn():
        val = responses.pop(0)
        if isinstance(val, Exception):
            raise val
        return val

    with_retry(fn, RetryConfig(max_attempts=3, backoff_factor=1.0), _sleep=fake_sleep)
    assert len(recorded) == 1
    assert recorded[0] == 1.0


def test_single_attempt_no_retry():
    def fn():
        raise OSError("fail")

    with pytest.raises(OSError):
        with_retry(fn, RetryConfig(max_attempts=1), _sleep=_fake_sleep)
