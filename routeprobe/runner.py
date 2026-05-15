"""Route probe runner — executes HTTP requests against loaded spec routes."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

import requests


@dataclass
class ProbeResult:
    """Result of probing a single route."""

    method: str
    path: str
    expected_status: int
    actual_status: Optional[int] = None
    passed: bool = False
    error: Optional[str] = None
    elapsed_ms: float = 0.0

    @property
    def label(self) -> str:
        return f"{self.method.upper()} {self.path}"


@dataclass
class RunReport:
    """Aggregated report for a full spec run."""

    results: List[ProbeResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return len(self.results) - self.passed

    @property
    def success(self) -> bool:
        return self.failed == 0


class ProbeRunner:
    """Runs all routes defined in a spec against the base URL."""

    def __init__(self, spec: dict, timeout: float = 10.0) -> None:
        self._spec = spec
        self._timeout = timeout
        self._session = requests.Session()

    def run(self) -> RunReport:
        """Execute all routes and return a RunReport."""
        base_url = self._spec["base_url"].rstrip("/")
        routes = self._spec.get("routes", [])
        report = RunReport()

        for route in routes:
            result = self._probe(base_url, route)
            report.results.append(result)

        return report

    def _probe(self, base_url: str, route: dict) -> ProbeResult:
        method = route["method"].upper()
        path = route["path"]
        expected_status = route["expected_status"]
        headers = route.get("headers", {})
        body = route.get("body", None)
        url = base_url + path

        result = ProbeResult(
            method=method,
            path=path,
            expected_status=expected_status,
        )

        try:
            start = time.perf_counter()
            response = self._session.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                timeout=self._timeout,
            )
            result.elapsed_ms = (time.perf_counter() - start) * 1000
            result.actual_status = response.status_code
            result.passed = response.status_code == expected_status
        except requests.exceptions.RequestException as exc:
            result.error = str(exc)
            result.passed = False

        return result
