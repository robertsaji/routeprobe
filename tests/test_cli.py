"""Tests for routeprobe.cli."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from routeprobe.cli import build_parser, main
from routeprobe.runner import ProbeResult, RunReport


def _make_report(*, failed: int = 0) -> RunReport:
    results = [
        ProbeResult(
            route_id="get-root",
            method="GET",
            url="http://example.com/",
            passed=(failed == 0),
            status_code=200 if failed == 0 else 500,
            failures=[] if failed == 0 else ["status mismatch"],
            error=None,
        )
    ]
    return RunReport(results=results)


def test_build_parser_defaults() -> None:
    parser = build_parser()
    args = parser.parse_args(["spec.yaml"])
    assert args.spec == "spec.yaml"
    assert args.format == "text"
    assert args.tags is None
    assert args.export is None
    assert args.export_format is None


def test_build_parser_json_format() -> None:
    args = build_parser().parse_args(["spec.yaml", "--format", "json"])
    assert args.format == "json"


def test_build_parser_tags() -> None:
    args = build_parser().parse_args(["spec.yaml", "--tags", "read", "write"])
    assert args.tags == ["read", "write"]


def test_build_parser_export_flags() -> None:
    args = build_parser().parse_args(
        ["spec.yaml", "--export", "out.xml", "--export-format", "junit"]
    )
    assert args.export == "out.xml"
    assert args.export_format == "junit"


def test_main_returns_zero_on_all_pass() -> None:
    report = _make_report(failed=0)
    with patch("routeprobe.cli.load_spec", return_value={"base_url": "http://x", "routes": []}):
        with patch("routeprobe.cli.run_routes", return_value=report):
            assert main(["spec.yaml"]) == 0


def test_main_returns_one_on_failure() -> None:
    report = _make_report(failed=1)
    with patch("routeprobe.cli.load_spec", return_value={"base_url": "http://x", "routes": []}):
        with patch("routeprobe.cli.run_routes", return_value=report):
            assert main(["spec.yaml"]) == 1


def test_main_export_creates_json_file(tmp_path: Path) -> None:
    dest = tmp_path / "report.json"
    report = _make_report()
    with patch("routeprobe.cli.load_spec", return_value={"base_url": "http://x", "routes": []}):
        with patch("routeprobe.cli.run_routes", return_value=report):
            rc = main(["spec.yaml", "--export", str(dest)])
    assert rc == 0
    assert dest.exists()
    data = json.loads(dest.read_text())
    assert "results" in data


def test_main_export_infers_junit_from_xml_extension(tmp_path: Path) -> None:
    dest = tmp_path / "report.xml"
    report = _make_report()
    with patch("routeprobe.cli.load_spec", return_value={"base_url": "http://x", "routes": []}):
        with patch("routeprobe.cli.run_routes", return_value=report):
            rc = main(["spec.yaml", "--export", str(dest)])
    assert rc == 0
    assert dest.exists()
    content = dest.read_text()
    assert "testsuite" in content


def test_main_returns_two_on_spec_load_error() -> None:
    with patch("routeprobe.cli.load_spec", side_effect=Exception("bad yaml")):
        with pytest.raises(Exception):
            main(["missing.yaml"])
