"""Tests for routeprobe.filter."""

from __future__ import annotations

import pytest

from routeprobe.filter import filter_routes, route_ids


ROUTES = [
    {"name": "list_users",   "method": "GET",    "path": "/users",   "tags": ["users", "read"]},
    {"name": "create_user",  "method": "POST",   "path": "/users",   "tags": ["users", "write"]},
    {"name": "health_check", "method": "GET",    "path": "/health",  "tags": ["ops"]},
    {"name": "delete_user",  "method": "DELETE", "path": "/users/1", "tags": ["users", "write"]},
]


# ---------------------------------------------------------------------------
# filter_routes — tag filtering
# ---------------------------------------------------------------------------

def test_filter_by_single_tag():
    result = filter_routes(ROUTES, tags=["ops"])
    assert len(result) == 1
    assert result[0]["name"] == "health_check"


def test_filter_by_multiple_tags_union():
    """Routes matching ANY of the supplied tags are returned."""
    result = filter_routes(ROUTES, tags=["read", "ops"])
    names = {r["name"] for r in result}
    assert names == {"list_users", "health_check"}


def test_filter_by_tag_returns_all_matching():
    result = filter_routes(ROUTES, tags=["users"])
    assert len(result) == 3


def test_filter_by_tag_no_match_returns_empty():
    result = filter_routes(ROUTES, tags=["nonexistent"])
    assert result == []


def test_filter_tag_case_insensitive():
    result = filter_routes(ROUTES, tags=["USERS"])
    assert len(result) == 3


# ---------------------------------------------------------------------------
# filter_routes — pattern filtering
# ---------------------------------------------------------------------------

def test_filter_by_exact_pattern():
    result = filter_routes(ROUTES, pattern="health_check")
    assert len(result) == 1
    assert result[0]["name"] == "health_check"


def test_filter_by_glob_pattern():
    result = filter_routes(ROUTES, pattern="*user*")
    names = {r["name"] for r in result}
    assert names == {"list_users", "create_user", "delete_user"}


def test_filter_pattern_case_insensitive():
    result = filter_routes(ROUTES, pattern="HEALTH*")
    assert len(result) == 1


def test_filter_pattern_no_match():
    result = filter_routes(ROUTES, pattern="xyz*")
    assert result == []


# ---------------------------------------------------------------------------
# filter_routes — combined tag + pattern
# ---------------------------------------------------------------------------

def test_filter_combined_tag_and_pattern():
    result = filter_routes(ROUTES, tags=["write"], pattern="create*")
    assert len(result) == 1
    assert result[0]["name"] == "create_user"


# ---------------------------------------------------------------------------
# filter_routes — no filters returns all
# ---------------------------------------------------------------------------

def test_no_filters_returns_all():
    result = filter_routes(ROUTES)
    assert result == ROUTES


# ---------------------------------------------------------------------------
# route_ids
# ---------------------------------------------------------------------------

def test_route_ids_uses_name_when_present():
    ids = route_ids(ROUTES)
    assert ids[0] == "list_users"


def test_route_ids_fallback_to_method_path():
    routes = [{"method": "GET", "path": "/ping"}]
    assert route_ids(routes) == ["GET /ping"]
