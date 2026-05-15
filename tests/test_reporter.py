"""Tests for routeprobe.reporter."""

from __future__ import annotations

import json

import pytest

from routeprobe.runner import ProbeResult, RunReport
from routeprobe.reporter import ReportFormatter, render_report


def _make_report(results: list[ProbeResult]) -> RunReport:
    passed = sum(1 for r in results if r.passed)
    return RunReport(results=results, total=len(results), passed=passed, failed=len(results) - passed)


def _pass_result(label: str = "GET /health") -> ProbeResult:
    return ProbeResult(label=label, passed=True, expected_status=200, actual_status=200, error=None)


def _fail_result(label: str = "POST /items", error: str | None = None) -> ProbeResult:
    return ProbeResult(label=label, passed=False, expected_status=201, actual_status=500, error=error)


def test_text_render_contains_summary():
    report = _make_report([_pass_result(), _fail_result()])
    output = render_report(report, fmt="text")
    assert "2 probe(s) run" in output
    assert "Passed: 1" in output
    assert "Failed: 1" in output


def test_text_render_pass_label():
    report = _make_report([_pass_result("GET /health")])
    output = render_report(report, fmt="text")
    assert "[PASS]" in output
    assert "GET /health" in output


def test_text_render_fail_shows_status_codes():
    report = _make_report([_fail_result()])
    output = render_report(report, fmt="text")
    assert "[FAIL]" in output
    assert "201" in output
    assert "500" in output


def test_text_render_fail_shows_error_message():
    report = _make_report([_fail_result(error="Connection refused")])
    output = render_report(report, fmt="text")
    assert "Connection refused" in output


def test_json_render_structure():
    report = _make_report([_pass_result(), _fail_result()])
    output = render_report(report, fmt="json")
    data = json.loads(output)
    assert data["total"] == 2
    assert data["passed"] == 1
    assert data["failed"] == 1
    assert len(data["results"]) == 2


def test_json_render_result_fields():
    report = _make_report([_pass_result("GET /ping")])
    data = json.loads(render_report(report, fmt="json"))
    result = data["results"][0]
    assert result["label"] == "GET /ping"
    assert result["passed"] is True
    assert result["expected_status"] == 200
    assert result["actual_status"] == 200
    assert result["error"] is None


def test_formatter_class_matches_convenience_fn():
    report = _make_report([_pass_result()])
    assert ReportFormatter(report, "text").render() == render_report(report, fmt="text")
    assert ReportFormatter(report, "json").render() == render_report(report, fmt="json")
