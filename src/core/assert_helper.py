import jsonschema

from src.schema.error_schema import ERROR_SCHEMA
from src.utils.redaction import redact, safe_body


class AssertHelper:
    """Every assertion in generated tests/helpers goes through here — never a bare `assert`."""

    @staticmethod
    def assert_schema(instance, schema: dict):
        try:
            jsonschema.validate(instance=instance, schema=schema)
        except jsonschema.ValidationError as e:
            raise AssertionError(f"Schema validation failed: {e.message}. Instance: {redact(instance)!r}"[:1500]) from e

    @staticmethod
    def assert_response(response, status_code: int, success_schema: dict, message: str | None = None):
        """The standard check every helper runs: the status first, then the success schema on a 2xx
        or the standard error schema (and, if given, the exact error message) otherwise."""
        AssertHelper.assert_status_code(response, status_code)
        body = response.json()
        if 200 <= status_code < 300:
            AssertHelper.assert_schema(body, success_schema)
        else:
            AssertHelper.assert_schema(body, ERROR_SCHEMA)
            if message is not None:
                AssertHelper.assert_field_equals(body, "message", message)
        return response

    @staticmethod
    def assert_status_code(response, expected: int):
        assert response.status_code == expected, (
            f"Expected status {expected}, got {response.status_code}. Body: {safe_body(response)}"
        )

    @staticmethod
    def assert_status_code_in(response, expected_codes):
        assert response.status_code in expected_codes, (
            f"Expected status in {expected_codes}, got {response.status_code}. Body: {safe_body(response)}"
        )

    @staticmethod
    def assert_content_type(response, expected_substring: str = "application/json"):
        content_type = response.headers.get("Content-Type", "")
        assert expected_substring in content_type, (
            f"Expected Content-Type containing '{expected_substring}', got '{content_type}'"
        )

    @staticmethod
    def assert_equals(actual, expected, context: str = ""):
        assert actual == expected, f"Expected {context}{expected!r}, got {actual!r}"

    @staticmethod
    def assert_not_equal(actual, unexpected, context: str = ""):
        assert actual != unexpected, f"Expected {context}to differ from {unexpected!r}, both were {actual!r}"

    @staticmethod
    def assert_true(condition: bool, message: str):
        assert condition, message

    @staticmethod
    def assert_is_instance(value, expected_type, context: str = ""):
        assert isinstance(value, expected_type), (
            f"Expected {context}to be of type {expected_type.__name__}, got {type(value).__name__} ({value!r})"
        )

    @staticmethod
    def assert_field_equals(body: dict, field: str, expected, path: str = ""):
        actual = body.get(field)
        assert actual == expected, f"Expected {path}{field}={expected!r}, got {actual!r}. Full body: {redact(body)}"

    @staticmethod
    def assert_field_present(body: dict, field: str, path: str = ""):
        assert field in body, f"Expected field {path}{field} to be present. Full body: {redact(body)}"

    @staticmethod
    def assert_field_absent(body: dict, field: str, path: str = ""):
        # The value is never echoed: this check exists to catch leaked secrets and personal data.
        assert field not in body, f"Expected field {path}{field} to be absent, but it is present (value withheld)"

    @staticmethod
    def assert_contains(haystack, needle, context: str = ""):
        assert needle in haystack, f"Expected {context}to contain {needle!r}, got {haystack!r}"

    @staticmethod
    def assert_not_contains(haystack, needle, context: str = ""):
        assert needle not in haystack, f"Expected {context}not to contain {needle!r}, got {haystack!r}"

    @staticmethod
    def assert_greater(actual, threshold, context: str = ""):
        assert actual > threshold, f"Expected {context}to be greater than {threshold!r}, got {actual!r}"

    @staticmethod
    def assert_greater_or_equal(actual, threshold, context: str = ""):
        assert actual >= threshold, f"Expected {context}to be at least {threshold!r}, got {actual!r}"
