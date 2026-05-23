"""Pre/post request hooks for routeprobe.

Hooks allow users to inject custom logic before a request is sent
or after a response is received, without modifying core runner logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional
import logging

log = logging.getLogger(__name__)

# Hook signatures
# pre_request(route: dict) -> dict   — may mutate/replace route headers, params
# post_response(route: dict, response) -> None — inspect or log response

PreRequestHook = Callable[[dict], dict]
PostResponseHook = Callable[[dict, object], None]


@dataclass
class HookRegistry:
    """Holds ordered lists of pre-request and post-response hooks."""

    _pre: List[PreRequestHook] = field(default_factory=list)
    _post: List[PostResponseHook] = field(default_factory=list)

    def register_pre(self, fn: PreRequestHook) -> PreRequestHook:
        """Register a pre-request hook. Returns the function (usable as decorator)."""
        if not callable(fn):
            raise TypeError(f"pre-request hook must be callable, got {type(fn)}")
        self._pre.append(fn)
        log.debug("Registered pre-request hook: %s", getattr(fn, "__name__", fn))
        return fn

    def register_post(self, fn: PostResponseHook) -> PostResponseHook:
        """Register a post-response hook. Returns the function (usable as decorator)."""
        if not callable(fn):
            raise TypeError(f"post-response hook must be callable, got {type(fn)}")
        self._post.append(fn)
        log.debug("Registered post-response hook: %s", getattr(fn, "__name__", fn))
        return fn

    def run_pre(self, route: dict) -> dict:
        """Run all pre-request hooks in registration order.

        Each hook receives the (possibly modified) route dict from the
        previous hook and must return a dict.
        """
        for hook in self._pre:
            result = hook(route)
            if not isinstance(result, dict):
                raise TypeError(
                    f"pre-request hook '{getattr(hook, '__name__', hook)}' "
                    f"must return a dict, got {type(result)}"
                )
            route = result
        return route

    def run_post(self, route: dict, response: object) -> None:
        """Run all post-response hooks in registration order."""
        for hook in self._post:
            try:
                hook(route, response)
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "post-response hook '%s' raised: %s",
                    getattr(hook, "__name__", hook),
                    exc,
                )

    def clear(self) -> None:
        """Remove all registered hooks (useful in tests)."""
        self._pre.clear()
        self._post.clear()

    @property
    def pre_count(self) -> int:
        return len(self._pre)

    @property
    def post_count(self) -> int:
        return len(self._post)
