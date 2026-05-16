"""Route filtering utilities for routeprobe.

Allows selecting a subset of routes from a spec based on tags or name patterns.
"""

from __future__ import annotations

import fnmatch
import re
from typing import List, Optional


def filter_routes(
    routes: List[dict],
    tags: Optional[List[str]] = None,
    pattern: Optional[str] = None,
) -> List[dict]:
    """Return routes matching the given tags and/or name pattern.

    Args:
        routes: List of route dicts loaded from a spec.
        tags:   If provided, only routes whose ``tags`` list contains at least
                one of the supplied tags are kept.
        pattern: If provided, only routes whose ``name`` field matches this
                 glob-style pattern (case-insensitive) are kept.

    Returns:
        Filtered list of route dicts.  Order is preserved.
    """
    result = routes

    if tags:
        normalised = {t.lower() for t in tags}
        result = [
            r for r in result
            if any(t.lower() in normalised for t in r.get("tags", []))
        ]

    if pattern:
        compiled = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        result = [r for r in result if compiled.match(r.get("name", ""))]

    return result


def route_ids(routes: List[dict]) -> List[str]:
    """Return a list of human-readable identifiers for the given routes.

    Each identifier is ``<method> <path>`` or the ``name`` field when present.
    """
    ids = []
    for r in routes:
        if "name" in r:
            ids.append(r["name"])
        else:
            ids.append(f"{r.get('method', 'GET').upper()} {r.get('path', '/')}")
    return ids
