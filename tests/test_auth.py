"""Tests for routeprobe.auth."""

import base64

import pytest

from routeprobe.auth import AuthConfig, AuthConfigError


# ---------------------------------------------------------------------------
# AuthConfig construction
# ---------------------------------------------------------------------------

class TestAuthConfigConstruction:
    def test_none_scheme_is_valid(self):
        cfg = AuthConfig(scheme="none")
        assert cfg.scheme == "none"

    def test_scheme_normalised_to_lowercase(self):
        cfg = AuthConfig(scheme="Bearer", token="tok")
        assert cfg.scheme == "bearer"

    def test_unknown_scheme_raises(self):
        with pytest.raises(AuthConfigError, match="Unknown auth scheme"):
            AuthConfig(scheme="oauth2")

    def test_bearer_without_token_raises(self):
        with pytest.raises(AuthConfigError, match="'bearer' scheme requires"):
            AuthConfig(scheme="bearer")

    def test_basic_without_credentials_raises(self):
        with pytest.raises(AuthConfigError, match="'basic' scheme requires"):
            AuthConfig(scheme="basic", username="user")

    def test_header_without_headers_raises(self):
        with pytest.raises(AuthConfigError, match="'header' scheme requires"):
            AuthConfig(scheme="header")


# ---------------------------------------------------------------------------
# AuthConfig.apply
# ---------------------------------------------------------------------------

class TestAuthConfigApply:
    def test_none_scheme_returns_headers_unchanged(self):
        cfg = AuthConfig(scheme="none")
        result = cfg.apply({"X-Custom": "value"})
        assert result == {"X-Custom": "value"}

    def test_bearer_adds_authorization_header(self):
        cfg = AuthConfig(scheme="bearer", token="mytoken")
        result = cfg.apply({})
        assert result["Authorization"] == "Bearer mytoken"

    def test_bearer_preserves_existing_headers(self):
        cfg = AuthConfig(scheme="bearer", token="t")
        result = cfg.apply({"Accept": "application/json"})
        assert "Accept" in result
        assert "Authorization" in result

    def test_basic_encodes_credentials(self):
        cfg = AuthConfig(scheme="basic", username="alice", password="secret")
        result = cfg.apply({})
        expected = base64.b64encode(b"alice:secret").decode()
        assert result["Authorization"] == f"Basic {expected}"

    def test_header_merges_custom_headers(self):
        cfg = AuthConfig(scheme="header", headers={"X-API-Key": "abc123"})
        result = cfg.apply({"Content-Type": "application/json"})
        assert result["X-API-Key"] == "abc123"
        assert result["Content-Type"] == "application/json"

    def test_apply_does_not_mutate_original(self):
        cfg = AuthConfig(scheme="bearer", token="t")
        original = {"Accept": "*/*"}
        cfg.apply(original)
        assert "Authorization" not in original


# ---------------------------------------------------------------------------
# AuthConfig.from_dict
# ---------------------------------------------------------------------------

class TestAuthConfigFromDict:
    def test_from_dict_bearer(self):
        cfg = AuthConfig.from_dict({"scheme": "bearer", "token": "mytoken"})
        assert cfg.scheme == "bearer"
        assert cfg.token == "mytoken"

    def test_from_dict_defaults_to_none_scheme(self):
        cfg = AuthConfig.from_dict({})
        assert cfg.scheme == "none"

    def test_from_dict_non_mapping_raises(self):
        with pytest.raises(AuthConfigError, match="must be a mapping"):
            AuthConfig.from_dict(["bearer", "token"])

    def test_from_dict_header_scheme(self):
        cfg = AuthConfig.from_dict(
            {"scheme": "header", "headers": {"X-Token": "xyz"}}
        )
        assert cfg.headers == {"X-Token": "xyz"}
