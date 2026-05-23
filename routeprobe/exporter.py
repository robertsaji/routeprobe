"""Export probe run reports to various file formats (JSON, JUnit XML)."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Literal

from routeprobe.runner import RunReport

ExportFormat = Literal["json", "junit"]


class ExportError(Exception):
    """Raised when an export operation fails."""


def export_report(report: RunReport, path: str | Path, fmt: ExportFormat) -> Path:
    """Write *report* to *path* in the requested *fmt*.

    Returns the resolved :class:`~pathlib.Path` that was written.
    Raises :class:`ExportError` on unsupported formats or I/O failures.
    """
    dest = Path(path)
    try:
        if fmt == "json":
            _write_json(report, dest)
        elif fmt == "junit":
            _write_junit(report, dest)
        else:
            raise ExportError(f"Unsupported export format: {fmt!r}")
    except OSError as exc:
        raise ExportError(f"Could not write to {dest}: {exc}") from exc
    return dest


def _write_json(report: RunReport, dest: Path) -> None:
    payload = {
        "total": report.total,
        "passed": report.passed,
        "failed": report.failed,
        "results": [
            {
                "route_id": r.route_id,
                "method": r.method,
                "url": r.url,
                "passed": r.passed,
                "status_code": r.status_code,
                "failures": r.failures,
                "error": r.error,
            }
            for r in report.results
        ],
    }
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_junit(report: RunReport, dest: Path) -> None:
    suite = ET.Element(
        "testsuite",
        name="routeprobe",
        tests=str(report.total),
        failures=str(report.failed),
        errors="0",
    )
    for r in report.results:
        case = ET.SubElement(
            suite,
            "testcase",
            classname="routeprobe",
            name=f"{r.method} {r.route_id}",
        )
        if not r.passed:
            messages = r.failures or ([r.error] if r.error else ["unknown error"])
            failure = ET.SubElement(case, "failure", message="; ".join(messages))
            failure.text = "\n".join(messages)
    tree = ET.ElementTree(suite)
    ET.indent(tree, space="  ")
    tree.write(str(dest), encoding="unicode", xml_declaration=True)
