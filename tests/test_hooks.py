"""Tests for routeprobe.hooks."""

import pytest
from routeprobe.hooks import HookRegistry


@pytest.fixture()
def registry():
    return HookRegistry()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_register_pre_returns_function(self, registry):
        fn = lambda route: route
        result = registry.register_pre(fn)
        assert result is fn

    def test_register_post_returns_function(self, registry):
        fn = lambda route, resp: None
        result = registry.register_post(fn)
        assert result is fn

    def test_counts_increment(self, registry):
        registry.register_pre(lambda r: r)
        registry.register_pre(lambda r: r)
        registry.register_post(lambda r, resp: None)
        assert registry.pre_count == 2
        assert registry.post_count == 1

    def test_non_callable_pre_raises(self, registry):
        with pytest.raises(TypeError, match="pre-request hook must be callable"):
            registry.register_pre("not_a_function")  # type: ignore[arg-type]

    def test_non_callable_post_raises(self, registry):
        with pytest.raises(TypeError, match="post-response hook must be callable"):
            registry.register_post(42)  # type: ignore[arg-type]

    def test_usable_as_decorator(self, registry):
        @registry.register_pre
        def add_header(route):
            route["headers"] = {"X-Test": "1"}
            return route

        assert registry.pre_count == 1


# ---------------------------------------------------------------------------
# run_pre
# ---------------------------------------------------------------------------

class TestRunPre:
    def test_no_hooks_returns_route_unchanged(self, registry):
        route = {"path": "/health"}
        assert registry.run_pre(route) == route

    def test_hook_can_add_header(self, registry):
        registry.register_pre(lambda r: {**r, "headers": {"X-Probe": "true"}})
        result = registry.run_pre({"path": "/ping"})
        assert result["headers"] == {"X-Probe": "true"}

    def test_hooks_run_in_order(self, registry):
        order = []
        registry.register_pre(lambda r: (order.append(1), r)[1])
        registry.register_pre(lambda r: (order.append(2), r)[1])
        registry.run_pre({})
        assert order == [1, 2]

    def test_hook_returning_non_dict_raises(self, registry):
        registry.register_pre(lambda r: "oops")  # type: ignore[return-value]
        with pytest.raises(TypeError, match="must return a dict"):
            registry.run_pre({"path": "/x"})

    def test_each_hook_receives_previous_output(self, registry):
        registry.register_pre(lambda r: {**r, "a": 1})
        registry.register_pre(lambda r: {**r, "b": 2})
        result = registry.run_pre({})
        assert result == {"a": 1, "b": 2}


# ---------------------------------------------------------------------------
# run_post
# ---------------------------------------------------------------------------

class TestRunPost:
    def test_no_hooks_does_not_raise(self, registry):
        registry.run_post({"path": "/health"}, object())

    def test_hook_receives_route_and_response(self, registry):
        captured = {}

        def capture(route, resp):
            captured["route"] = route
            captured["resp"] = resp

        registry.register_post(capture)
        fake_resp = object()
        registry.run_post({"path": "/x"}, fake_resp)
        assert captured["route"] == {"path": "/x"}
        assert captured["resp"] is fake_resp

    def test_failing_hook_does_not_propagate(self, registry):
        registry.register_post(lambda r, resp: (_ for _ in ()).throw(RuntimeError("boom")))
        # Should not raise
        registry.run_post({}, object())


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

def test_clear_removes_all_hooks(registry):
    registry.register_pre(lambda r: r)
    registry.register_post(lambda r, resp: None)
    registry.clear()
    assert registry.pre_count == 0
    assert registry.post_count == 0
