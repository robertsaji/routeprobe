"""Tests for routeprobe.timeout."""

import pytest

from routeprobe.timeout import (
    TimeoutConfig,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
)


class TestTimeoutConfigDefaults:
    def test_default_connect(self):
        cfg = TimeoutConfig()
        assert cfg.connect == DEFAULT_CONNECT_TIMEOUT

    def test_default_read(self):
        cfg = TimeoutConfig()
        assert cfg.read == DEFAULT_READ_TIMEOUT

    def test_as_tuple(self):
        cfg = TimeoutConfig(connect=3.0, read=7.0)
        assert cfg.as_tuple == (3.0, 7.0)

    def test_total(self):
        cfg = TimeoutConfig(connect=2.0, read=8.0)
        assert cfg.total == 10.0


class TestTimeoutConfigValidation:
    def test_zero_connect_raises(self):
        with pytest.raises(ValueError, match="connect timeout"):
            TimeoutConfig(connect=0)

    def test_negative_read_raises(self):
        with pytest.raises(ValueError, match="read timeout"):
            TimeoutConfig(read=-1)

    def test_positive_values_accepted(self):
        cfg = TimeoutConfig(connect=0.1, read=0.1)
        assert cfg.connect == 0.1


class TestTimeoutConfigFromDict:
    def test_no_key_returns_defaults(self):
        cfg = TimeoutConfig.from_dict({})
        assert cfg.connect == DEFAULT_CONNECT_TIMEOUT
        assert cfg.read == DEFAULT_READ_TIMEOUT

    def test_scalar_sets_read_only(self):
        cfg = TimeoutConfig.from_dict({"timeout": 20})
        assert cfg.read == 20.0
        assert cfg.connect == DEFAULT_CONNECT_TIMEOUT

    def test_float_scalar(self):
        cfg = TimeoutConfig.from_dict({"timeout": 3.5})
        assert cfg.read == 3.5

    def test_dict_sets_both(self):
        cfg = TimeoutConfig.from_dict({"timeout": {"connect": 2, "read": 15}})
        assert cfg.connect == 2.0
        assert cfg.read == 15.0

    def test_dict_partial_uses_defaults(self):
        cfg = TimeoutConfig.from_dict({"timeout": {"read": 12}})
        assert cfg.connect == DEFAULT_CONNECT_TIMEOUT
        assert cfg.read == 12.0

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Invalid timeout"):
            TimeoutConfig.from_dict({"timeout": "fast"})

    def test_as_tuple_after_from_dict(self):
        cfg = TimeoutConfig.from_dict({"timeout": {"connect": 1, "read": 5}})
        assert cfg.as_tuple == (1.0, 5.0)
