"""Tests for routeprobe.spec_loader."""

import textwrap
from pathlib import Path

import pytest

from routeprobe.spec_loader import load_spec, SpecLoadError


FIXTURES = Path(__file__).parent / "fixtures"


def test_load_valid_spec():
    spec = load_spec(FIXTURES / "sample_spec.yaml")
    assert spec["base_url"] == "https://api.example.com"
    assert len(spec["routes"]) == 3


def test_first_route_fields():
    spec = load_spec(FIXTURES / "sample_spec.yaml")
    route = spec["routes"][0]
    assert route["method"] == "GET"
    assert route["path"] == "/health"
    assert route["expect"]["status"] == 200


def test_missing_file_raises():
    with pytest.raises(SpecLoadError, match="not found"):
        load_spec("nonexistent_spec.yaml")


def test_invalid_yaml_raises(tmp_path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("base_url: [unclosed", encoding="utf-8")
    with pytest.raises(SpecLoadError, match="Failed to parse YAML"):
        load_spec(bad_yaml)


def test_missing_base_url_raises(tmp_path):
    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text("routes: []\n", encoding="utf-8")
    with pytest.raises(SpecLoadError, match="base_url"):
        load_spec(spec_file)


def test_missing_route_method_raises(tmp_path):
    content = textwrap.dedent("""\
        base_url: https://api.example.com
        routes:
          - path: /health
            expect:
              status: 200
    """)
    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(content, encoding="utf-8")
    with pytest.raises(SpecLoadError, match="method"):
        load_spec(spec_file)


def test_missing_expect_status_raises(tmp_path):
    content = textwrap.dedent("""\
        base_url: https://api.example.com
        routes:
          - method: GET
            path: /health
            expect:
              body: {}
    """)
    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(content, encoding="utf-8")
    with pytest.raises(SpecLoadError, match="status"):
        load_spec(spec_file)
