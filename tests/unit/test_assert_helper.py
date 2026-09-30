import pytest

from src.core.assert_helper import AssertHelper

pytestmark = pytest.mark.unit


class _FakeResponse:
    def __init__(self, status_code=200, body=None, content_type="application/json"):
        self.status_code, self._body, self.headers = status_code, body or {}, {"Content-Type": content_type}

    def json(self):
        return self._body


class TestAssertHelper:
    """AssertHelper raises AssertionError itself, so its checks survive `python -O` (which strips `assert`)."""

    @pytest.mark.parametrize(
        ("check", "args", "message"),
        [
            (AssertHelper.assert_equals, (1, 2), "Expected 2, got 1"),
            (AssertHelper.assert_not_equal, (1, 1), "Expected to differ from 1, both were 1"),
            (AssertHelper.assert_is_instance, ("1", int), "Expected to be of type int, got str ('1')"),
            (AssertHelper.assert_contains, ([1, 2], 3), "Expected to contain 3, got [1, 2]"),
            (AssertHelper.assert_greater, (1, 1), "Expected to be greater than 1, got 1"),
            (AssertHelper.assert_greater_or_equal, (0, 1), "Expected to be at least 1, got 0"),
        ],
    )
    def test_failed_check_raises_with_message(self, check, args, message):
        with pytest.raises(AssertionError) as error:
            check(*args)
        AssertHelper.assert_equals(str(error.value), message, "the failure message ")

    def test_passing_checks_return_none(self):
        AssertHelper.assert_equals(AssertHelper.assert_greater_or_equal(1, 1), None)
        AssertHelper.assert_equals(AssertHelper.assert_contains("abc", "b"), None)

    def test_field_equals_redacts_the_body(self):
        with pytest.raises(AssertionError) as error:
            AssertHelper.assert_field_equals({"id": 1, "password": "hunter2"}, "id", 2)
        AssertHelper.assert_equals(
            str(error.value), "Expected id=2, got 1. Full body: {'id': 1, 'password': '***'}", "the failure message "
        )

    def test_field_absent_never_echoes_the_value(self):
        with pytest.raises(AssertionError) as error:
            AssertHelper.assert_field_absent({"password": "hunter2"}, "password")
        AssertHelper.assert_equals("hunter2" in str(error.value), False, "value in the failure message ")

    def test_status_code_mismatch_redacts_the_body(self):
        with pytest.raises(AssertionError) as error:
            AssertHelper.assert_status_code(_FakeResponse(500, {"accessToken": "a.b.c"}), 200)
        AssertHelper.assert_equals(
            str(error.value), 'Expected status 200, got 500. Body: {"accessToken": "***"}', "the failure message "
        )

    def test_content_type_mismatch_raises(self):
        with pytest.raises(AssertionError, match="Expected Content-Type containing 'application/json'"):
            AssertHelper.assert_content_type(_FakeResponse(content_type="text/html"))

    def test_schema_failure_raises(self):
        with pytest.raises(AssertionError, match="Schema validation failed"):
            AssertHelper.assert_schema({"id": "1"}, {"type": "object", "properties": {"id": {"type": "integer"}}})
