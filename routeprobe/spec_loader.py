"""Load and validate a routeprobe YAML spec file."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


class SpecLoadError(Exception):
    """Raised when the spec file cannot be loaded or is structurally invalid."""


# Required top-level keys
_TOP_LEVEL_REQUIRED = {"base_url", "routes"}

# Required keys for every route entry
_ROUTE_REQUIRED = {"method", "path", "expected_status"}


def load_spec(path: str | Path) -> Dict[str, Any]:
    """Load a YAML spec file and return its contents as a dict.

    Args:
        path: Path to the ``.yaml`` spec file.

    Returns:
        Parsed spec dictionary with keys ``base_url`` and ``routes``.

    Raises:
        SpecLoadError: If the file is missing, not valid YAML, or fails
                       structural validation.
    """
    fpath = Path(path)

    try:
        raw = fpath.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SpecLoadError(f"Spec file not found: {fpath}")

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise SpecLoadError(f"Invalid YAML in spec file: {exc}") from exc

    if not isinstance(data, dict):
        raise SpecLoadError("Spec file must be a YAML mapping at the top level.")

    missing_top = _TOP_LEVEL_REQUIRED - data.keys()
    if missing_top:
        raise SpecLoadError(
            f"Spec is missing required top-level keys: {sorted(missing_top)}"
        )

    if not isinstance(data["routes"], list):
        raise SpecLoadError("'routes' must be a list.")

    for idx, route in enumerate(data["routes"]):
        _validate_route(route, idx)

    return data


def _validate_route(route: Any, idx: int) -> None:
    """Validate a single route entry.

    Args:
        route: The route value from the YAML list.
        idx:   Zero-based index used in error messages.

    Raises:
        SpecLoadError: If the route is not a dict or is missing required keys.
    """
    if not isinstance(route, dict):
        raise SpecLoadError(f"Route at index {idx} must be a mapping, got {type(route).__name__}.")

    missing = _ROUTE_REQUIRED - route.keys()
    if missing:
        raise SpecLoadError(
            f"Route at index {idx} is missing required keys: {sorted(missing)}"
        )
