"""Tests for routeprobe.validator."""

import pytest

from routeprobe.validator import ValidationResult, validate_response


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

class TestValidationResult:
    def test_passed_is_truthy(self):
        assert ValidationResult(passed=True)

    def test_failed_is_falsy(self):
        assert not ValidationResult(passed=False, failures=["oops"])

    def test_default_failures_empty(self):
        result = ValidationResult(passed=True)
        assert result.failures == []


# ---------------------------------------------------------------------------
# validate_response — status code
# ---------------------------------------------------------------------------

class TestStatusCodeValidation:
    def test_matching_status_passes(self):
        result = validate_response(200, None, expected_status=200)
        assert result.passed
        assert result.failures == []

    def test_mismatched_status_fails(self):
        result = validate_response(404, None, expected_status=200)
        assert not result.passed
        assert any("status code" in f for f in result.failures)

    def test_no_expected_status_skips_check(self):
        result = validate_response(500, None, expected_status=None)
        assert result.passed

    def test_failure_message_contains_both_codes(self):
        result = validate_response(503, None, expected_status=200)
        assert "503" in result.failures[0]
        assert "200" in result.failures[0]


# ---------------------------------------------------------------------------
# validate_response — JSON key checks
# ---------------------------------------------------------------------------

class TestJsonKeyValidation:
    def test_all_keys_present_passes(self):
        body = {"id": 1, "name": "alice"}
        result = validate_response(200, body, expected_status=200, expected_json_keys=["id", "name"])
        assert result.passed

    def test_missing_key_fails(self):
        body = {"id": 1}
        result = validate_response(200, body, expected_status=200, expected_json_keys=["id", "name"])
        assert not result.passed
        assert any("name" in f for f in result.failures)

    def test_non_dict_body_fails_key_check(self):
        result = validate_response(200, [1, 2, 3], expected_status=200, expected_json_keys=["id"])
        assert not result.passed
        assert any("JSON object" in f for f in result.failures)

    def test_none_body_fails_key_check(self):
        result = validate_response(200, None, expected_status=200, expected_json_keys=["id"])
        assert not result.passed

    def test_no_key_check_when_list_is_none(self):
        result = validate_response(200, {"id": 1}, expected_status=200, expected_json_keys=None)
        assert result.passed

    def test_multiple_missing_keys_reported(self):
        body = {}
        result = validate_response(200, body, expected_status=200, expected_json_keys=["a", "b", "c"])
        assert not result.passed
        failure_text = " ".join(result.failures)
        assert "a" in failure_text and "b" in failure_text and "c" in failure_text


# ---------------------------------------------------------------------------
# Combined failures
# ---------------------------------------------------------------------------

class TestCombinedValidation:
    def test_both_status_and_key_failures_reported(self):
        body = {}
        result = validate_response(404, body, expected_status=200, expected_json_keys=["id"])
        assert not result.passed
        assert len(result.failures) == 2
