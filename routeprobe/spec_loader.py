"""Loads and validates a YAML API spec for routeprobe."""

import yaml
from pathlib import Path
from typing import Any


REQUIRED_ROUTE_FIELDS = {"method", "path", "expect"}
REQUIRED_EXPECT_FIELDS = {"status"}


class SpecLoadError(Exception):
    """Raised when the YAML spec is missing or malformed."""


def load_spec(spec_path: str | Path) -> dict[str, Any]:
    """Load and parse a YAML spec file.

    Args:
        spec_path: Path to the YAML spec file.

    Returns:
        Parsed spec as a dictionary.

    Raises:
        SpecLoadError: If the file is missing, unreadable, or structurally invalid.
    """
    path = Path(spec_path)
    if not path.exists():
        raise SpecLoadError(f"Spec file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise SpecLoadError(f"Failed to parse YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise SpecLoadError("Spec root must be a YAML mapping.")

    if "base_url" not in data:
        raise SpecLoadError("Spec must define 'base_url'.")

    routes = data.get("routes", [])
    if not isinstance(routes, list):
        raise SpecLoadError("'routes' must be a list.")

    for i, route in enumerate(routes):
        _validate_route(route, index=i)

    return data


def _validate_route(route: Any, index: int) -> None:
    if not isinstance(route, dict):
        raise SpecLoadError(f"Route at index {index} must be a mapping.")

    missing = REQUIRED_ROUTE_FIELDS - route.keys()
    if missing:
        raise SpecLoadError(
            f"Route at index {index} is missing required fields: {missing}"
        )

    expect = route["expect"]
    if not isinstance(expect, dict):
        raise SpecLoadError(f"Route at index {index}: 'expect' must be a mapping.")

    missing_expect = REQUIRED_EXPECT_FIELDS - expect.keys()
    if missing_expect:
        raise SpecLoadError(
            f"Route at index {index}: 'expect' is missing fields: {missing_expect}"
        )
