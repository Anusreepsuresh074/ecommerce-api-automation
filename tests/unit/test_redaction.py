import json

import pytest

from src.core.assert_helper import AssertHelper
from src.utils.redaction import is_sensitive_key, redact, redact_headers, safe_body

pytestmark = pytest.mark.unit


class _FakeResponse:
    def __init__(self, body=None, text=""):
        self._body, self.text = body, text

    def json(self):
        if self._body is None:
            raise ValueError("not JSON")
        return self._body


class TestRedaction:
    @pytest.mark.parametrize("key", ["password", "Password", "accessToken", "refreshToken", "client_secret"])
    def test_credential_keys_are_sensitive(self, key):
        AssertHelper.assert_equals(is_sensitive_key(key), True, f"is_sensitive_key({key!r}) ")

    @pytest.mark.parametrize("key", ["username", "id", "email", "expiresInMins"])
    def test_ordinary_keys_are_not_sensitive(self, key):
        AssertHelper.assert_equals(is_sensitive_key(key), False, f"is_sensitive_key({key!r}) ")

    def test_passwords_and_tokens_are_masked(self):
        body = {"username": "emilys", "password": "hunter2", "accessToken": "a.b.c", "refreshToken": "d.e.f"}
        AssertHelper.assert_equals(
            redact(body), {"username": "emilys", "password": "***", "accessToken": "***", "refreshToken": "***"}
        )

    def test_nested_dicts_and_lists_are_masked(self):
        body = {"users": [{"id": 1, "auth": {"token": "x.y.z"}}, {"id": 2, "password": "p"}], "total": 2}
        AssertHelper.assert_equals(
            redact(body), {"users": [{"id": 1, "auth": {"token": "***"}}, {"id": 2, "password": "***"}], "total": 2}
        )

    def test_a_sensitive_key_masks_its_whole_value(self):
        # A nested object under a credential key is replaced outright, not walked into.
        AssertHelper.assert_equals(redact({"tokens": {"access": "a", "refresh": "r"}}), {"tokens": "***"})

    def test_input_is_not_modified(self):
        body = {"password": "hunter2"}
        redact(body)
        AssertHelper.assert_equals(body, {"password": "hunter2"}, "the original body ")

    @pytest.mark.parametrize("value", ["plain", 42, None, True])
    def test_scalars_pass_through(self, value):
        AssertHelper.assert_equals(redact(value), value)

    def test_authorization_and_cookie_headers_are_masked_in_any_case(self):
        headers = {"Authorization": "Bearer a.b.c", "cookie": "accessToken=a.b.c", "Content-Type": "application/json"}
        AssertHelper.assert_equals(
            redact_headers(headers), {"Authorization": "***", "cookie": "***", "Content-Type": "application/json"}
        )

    @pytest.mark.parametrize("headers", [None, {}])
    def test_no_headers_pass_through(self, headers):
        AssertHelper.assert_equals(redact_headers(headers), headers)

    def test_safe_body_masks_credentials_in_json(self):
        text = safe_body(_FakeResponse({"accessToken": "a.b.c", "id": 1}))
        AssertHelper.assert_equals(json.loads(text), {"accessToken": "***", "id": 1})

    def test_safe_body_truncates(self):
        AssertHelper.assert_equals(len(safe_body(_FakeResponse({"data": "x" * 1000}), limit=50)), 50)

    def test_safe_body_falls_back_to_text_for_non_json(self):
        AssertHelper.assert_equals(safe_body(_FakeResponse(text="<html>oops</html>")), "<html>oops</html>")
