"""Authentication helpers for routeprobe HTTP requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


class AuthConfigError(ValueError):
    """Raised when an auth configuration is invalid."""


@dataclass
class AuthConfig:
    """Holds authentication configuration for outgoing requests."""

    scheme: str  # "bearer", "basic", "header", "none"
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)

    _VALID_SCHEMES = {"bearer", "basic", "header", "none"}

    def __post_init__(self) -> None:
        scheme = self.scheme.lower()
        if scheme not in self._VALID_SCHEMES:
            raise AuthConfigError(
                f"Unknown auth scheme '{self.scheme}'. "
                f"Expected one of: {sorted(self._VALID_SCHEMES)}"
            )
        self.scheme = scheme

        if self.scheme == "bearer" and not self.token:
            raise AuthConfigError("'bearer' scheme requires a non-empty 'token'.")

        if self.scheme == "basic" and not (self.username and self.password):
            raise AuthConfigError(
                "'basic' scheme requires both 'username' and 'password'."
            )

        if self.scheme == "header" and not self.headers:
            raise AuthConfigError(
                "'header' scheme requires at least one entry in 'headers'."
            )

    def apply(self, existing_headers: Dict[str, str]) -> Dict[str, str]:
        """Return a new headers dict with auth credentials merged in."""
        merged = dict(existing_headers)

        if self.scheme == "none":
            return merged

        if self.scheme == "bearer":
            merged["Authorization"] = f"Bearer {self.token}"

        elif self.scheme == "basic":
            import base64
            credentials = base64.b64encode(
                f"{self.username}:{self.password}".encode()
            ).decode()
            merged["Authorization"] = f"Basic {credentials}"

        elif self.scheme == "header":
            merged.update(self.headers)

        return merged

    @classmethod
    def from_dict(cls, data: dict) -> "AuthConfig":
        """Construct an AuthConfig from a plain dictionary (e.g. parsed YAML)."""
        if not isinstance(data, dict):
            raise AuthConfigError("Auth configuration must be a mapping.")
        scheme = data.get("scheme", "none")
        return cls(
            scheme=scheme,
            token=data.get("token"),
            username=data.get("username"),
            password=data.get("password"),
            headers=data.get("headers", {}),
        )
