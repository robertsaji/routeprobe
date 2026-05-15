"""Tests for routeprobe.runner."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from routeprobe.runner import ProbeResult, ProbeRunner, RunReport


SAMPLE_SPEC = {
    "base_url": "https://api.example.com",
    "routes": [
        {"method": "GET", "path": "/health", "expected_status": 200},
        {"method": "POST", "path": "/users", "expected_status": 201,
         "body": {"name": "Alice"}},
    ],
}


def _make_response(status_code: int) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    return resp


@patch("routeprobe.runner.requests.Session.request")
def test_run_all_pass(mock_request):
    mock_request.side_effect = [
        _make_response(200),
        _make_response(201),
    ]
    runner = ProbeRunner(SAMPLE_SPEC)
    report = runner.run()

    assert len(report.results) == 2
    assert report.passed == 2
    assert report.failed == 0
    assert report.success is True


@patch("routeprobe.runner.requests.Session.request")
def test_run_partial_failure(mock_request):
    mock_request.side_effect = [
        _make_response(200),
        _make_response(500),  # unexpected
    ]
    runner = ProbeRunner(SAMPLE_SPEC)
    report = runner.run()

    assert report.passed == 1
    assert report.failed == 1
    assert report.success is False


@patch("routeprobe.runner.requests.Session.request")
def test_network_error_marks_failed(mock_request):
    mock_request.side_effect = requests.exceptions.ConnectionError("refused")
    spec = {
        "base_url": "https://api.example.com",
        "routes": [{"method": "GET", "path": "/ping", "expected_status": 200}],
    }
    runner = ProbeRunner(spec)
    report = runner.run()

    result = report.results[0]
    assert result.passed is False
    assert result.actual_status is None
    assert "refused" in result.error


@patch("routeprobe.runner.requests.Session.request")
def test_probe_result_label(mock_request):
    mock_request.return_value = _make_response(200)
    spec = {
        "base_url": "https://api.example.com",
        "routes": [{"method": "get", "path": "/items", "expected_status": 200}],
    }
    runner = ProbeRunner(spec)
    report = runner.run()

    assert report.results[0].label == "GET /items"


def test_run_report_empty():
    report = RunReport()
    assert report.passed == 0
    assert report.failed == 0
    assert report.success is True
