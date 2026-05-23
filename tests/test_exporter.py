"""Tests for routeprobe.exporter."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from routeprobe.exporter import ExportError, export_report
from routeprobe.runner import ProbeResult, RunReport


def _make_report() -> RunReport:
    results = [
        ProbeResult(
            route_id="get-users",
            method="GET",
            url="http://api.example.com/users",
            passed=True,
            status_code=200,
            failures=[],
            error=None,
        ),
        ProbeResult(
            route_id="post-login",
            method="POST",
            url="http://api.example.com/login",
            passed=False,
            status_code=500,
            failures=["expected status 200, got 500"],
            error=None,
        ),
    ]
    return RunReport(results=results)


class TestExportJson:
    def test_creates_file(self, tmp_path: Path) -> None:
        dest = tmp_path / "report.json"
        export_report(_make_report(), dest, "json")
        assert dest.exists()

    def test_json_structure(self, tmp_path: Path) -> None:
        dest = tmp_path / "report.json"
        export_report(_make_report(), dest, "json")
        data = json.loads(dest.read_text())
        assert data["total"] == 2
        assert data["passed"] == 1
        assert data["failed"] == 1
        assert len(data["results"]) == 2

    def test_result_fields_present(self, tmp_path: Path) -> None:
        dest = tmp_path / "report.json"
        export_report(_make_report(), dest, "json")
        first = json.loads(dest.read_text())["results"][0]
        assert first["route_id"] == "get-users"
        assert first["passed"] is True
        assert first["status_code"] == 200


class TestExportJunit:
    def test_creates_file(self, tmp_path: Path) -> None:
        dest = tmp_path / "report.xml"
        export_report(_make_report(), dest, "junit")
        assert dest.exists()

    def test_xml_has_testsuite(self, tmp_path: Path) -> None:
        dest = tmp_path / "report.xml"
        export_report(_make_report(), dest, "junit")
        tree = ET.parse(dest)
        root = tree.getroot()
        assert root.tag == "testsuite"
        assert root.attrib["tests"] == "2"
        assert root.attrib["failures"] == "1"

    def test_failed_case_has_failure_element(self, tmp_path: Path) -> None:
        dest = tmp_path / "report.xml"
        export_report(_make_report(), dest, "junit")
        tree = ET.parse(dest)
        cases = tree.findall("testcase")
        failed = [c for c in cases if c.find("failure") is not None]
        assert len(failed) == 1
        assert "500" in failed[0].find("failure").text


class TestExportErrors:
    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ExportError, match="Unsupported"):
            export_report(_make_report(), tmp_path / "out.csv", "csv")  # type: ignore[arg-type]

    def test_bad_path_raises(self) -> None:
        with pytest.raises(ExportError, match="Could not write"):
            export_report(_make_report(), "/no/such/directory/out.json", "json")

    def test_returns_resolved_path(self, tmp_path: Path) -> None:
        dest = tmp_path / "report.json"
        result = export_report(_make_report(), dest, "json")
        assert result == dest.resolve()
