"""Timeout configuration and enforcement for HTTP probes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_READ_TIMEOUT = 10.0


@dataclass
class TimeoutConfig:
    """Per-request timeout settings (seconds)."""

    connect: float = DEFAULT_CONNECT_TIMEOUT
    read: float = DEFAULT_READ_TIMEOUT

    def __post_init__(self) -> None:
        if self.connect <= 0:
            raise ValueError(f"connect timeout must be positive, got {self.connect}")
        if self.read <= 0:
            raise ValueError(f"read timeout must be positive, got {self.read}")

    @property
    def as_tuple(self) -> tuple[float, float]:
        """Return (connect, read) tuple accepted by *requests*."""
        return (self.connect, self.read)

    @property
    def total(self) -> float:
        """Upper-bound wall-clock time for a single request."""
        return self.connect + self.read

    @classmethod
    def from_dict(cls, data: dict) -> "TimeoutConfig":
        """Build a TimeoutConfig from a route-level YAML mapping.

        Accepted keys: ``timeout`` (scalar → read only) or
        ``timeout: {connect: N, read: N}``.
        """
        raw = data.get("timeout")
        if raw is None:
            return cls()
        if isinstance(raw, (int, float)):
            return cls(read=float(raw))
        if isinstance(raw, dict):
            return cls(
                connect=float(raw.get("connect", DEFAULT_CONNECT_TIMEOUT)),
                read=float(raw.get("read", DEFAULT_READ_TIMEOUT)),
            )
        raise ValueError(f"Invalid timeout value: {raw!r}")

    def __repr__(self) -> str:  # pragma: no cover
        return f"TimeoutConfig(connect={self.connect}, read={self.read})"
