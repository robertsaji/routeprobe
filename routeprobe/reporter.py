"""Report formatting for RouteProbe run results."""

from __future__ import annotations

import json
from typing import Literal

from routeprobe.runner import RunReport

OutputFormat = Literal["text", "json"]


class ReportFormatter:
    """Formats a RunReport into human-readable or machine-readable output."""

    def __init__(self, report: RunReport, fmt: OutputFormat = "text") -> None:
        self.report = report
        self.fmt = fmt

    def render(self) -> str:
        if self.fmt == "json":
            return self._render_json()
        return self._render_text()

    def _render_text(self) -> str:
        lines: list[str] = []
        lines.append(f"RouteProbe Report — {self.report.total} probe(s) run")
        lines.append("-" * 40)
        for result in self.report.results:
            status = "PASS" if result.passed else "FAIL"
            line = f"  [{status}] {result.label}"
            if not result.passed and result.error:
                line += f" — {result.error}"
            elif not result.passed:
                line += f" — expected {result.expected_status}, got {result.actual_status}"
            lines.append(line)
        lines.append("-" * 40)
        lines.append(f"Passed: {self.report.passed}  Failed: {self.report.failed}")
        return "\n".join(lines)

    def _render_json(self) -> str:
        data = {
            "total": self.report.total,
            "passed": self.report.passed,
            "failed": self.report.failed,
            "results": [
                {
                    "label": r.label,
                    "passed": r.passed,
                    "expected_status": r.expected_status,
                    "actual_status": r.actual_status,
                    "error": r.error,
                }
                for r in self.report.results
            ],
        }
        return json.dumps(data, indent=2)


def render_report(report: RunReport, fmt: OutputFormat = "text") -> str:
    """Convenience wrapper around ReportFormatter."""
    return ReportFormatter(report, fmt).render()
