"""Tests for routeprobe.cli."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from routeprobe.cli import build_parser, main
from routeprobe.runner import ProbeResult, RunReport
from routeprobe.spec_loader import SpecLoadError


SAMPLE_SPEC_PATH = "tests/fixtures/sample_spec.yaml"


def _make_report(passed: int = 2, failed: int = 0) -> RunReport:
    results = [
        ProbeResult(label=f"GET /route{i}", passed=True, expected_status=200, actual_status=200, error=None)
        for i in range(passed)
    ] + [
        ProbeResult(label=f"POST /bad{i}", passed=False, expected_status=201, actual_status=500, error=None)
        for i in range(failed)
    ]
    return RunReport(results=results, total=passed + failed, passed=passed, failed=failed)


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["spec.yaml"])
    assert args.spec == "spec.yaml"
    assert args.fmt == "text"
    assert args.fail_fast is False


def test_build_parser_json_format():
    parser = build_parser()
    args = parser.parse_args(["spec.yaml", "--format", "json"])
    assert args.fmt == "json"


def test_main_returns_zero_on_all_pass(capsys):
    with patch("routeprobe.cli.load_spec") as mock_load, \
         patch("routeprobe.cli.run_spec") as mock_run:
        mock_load.return_value = MagicMock()
        mock_run.return_value = _make_report(passed=2, failed=0)
        code = main(["spec.yaml"])
    assert code == 0


def test_main_returns_one_on_failure(capsys):
    with patch("routeprobe.cli.load_spec") as mock_load, \
         patch("routeprobe.cli.run_spec") as mock_run:
        mock_load.return_value = MagicMock()
        mock_run.return_value = _make_report(passed=1, failed=1)
        code = main(["spec.yaml"])
    assert code == 1


def test_main_returns_one_on_spec_load_error(capsys):
    with patch("routeprobe.cli.load_spec", side_effect=SpecLoadError("bad file")):
        code = main(["missing.yaml"])
    assert code == 1
    captured = capsys.readouterr()
    assert "bad file" in captured.err


def test_main_passes_fail_fast_to_runner():
    with patch("routeprobe.cli.load_spec") as mock_load, \
         patch("routeprobe.cli.run_spec") as mock_run:
        mock_load.return_value = MagicMock()
        mock_run.return_value = _make_report()
        main(["spec.yaml", "--fail-fast"])
        _, kwargs = mock_run.call_args
        assert kwargs.get("fail_fast") is True
