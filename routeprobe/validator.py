"""Response validation logic for routeprobe.

Validates actual HTTP responses against expected values defined in the spec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    """Outcome of validating a single response."""

    passed: bool
    failures: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.passed


def validate_response(
    status_code: int,
    body: Any,
    expected_status: int | None,
    expected_json_keys: list[str] | None = None,
) -> ValidationResult:
    """Validate an HTTP response against expected values from the spec.

    Args:
        status_code: The actual HTTP status code returned.
        body: The parsed JSON body of the response (or None).
        expected_status: The status code declared in the spec.
        expected_json_keys: Optional list of keys that must be present in the
            JSON response body.

    Returns:
        A :class:`ValidationResult` describing whether validation passed and
        any failure messages.
    """
    failures: list[str] = []

    if expected_status is not None and status_code != expected_status:
        failures.append(
            f"status code: expected {expected_status}, got {status_code}"
        )

    if expected_json_keys:
        if not isinstance(body, dict):
            failures.append(
                f"expected JSON object body to check keys {expected_json_keys}, "
                f"got {type(body).__name__}"
            )
        else:
            missing = [k for k in expected_json_keys if k not in body]
            if missing:
                failures.append(
                    f"missing expected JSON keys: {', '.join(missing)}"
                )

    return ValidationResult(passed=len(failures) == 0, failures=failures)
