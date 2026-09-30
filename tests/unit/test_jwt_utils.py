import base64
import json

import pytest

from src.core.assert_helper import AssertHelper
from src.utils.jwt_utils import decode_jwt_payload, tamper_signature

pytestmark = pytest.mark.unit


def _b64url(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")


def _make_token(claims: dict, signature: str = "c2lnbmF0dXJl") -> str:
    """An unsigned, locally built JWT: enough to exercise decoding, never sent anywhere."""
    return f"{_b64url({'alg': 'HS256', 'typ': 'JWT'})}.{_b64url(claims)}.{signature}"


class TestJwtUtils:
    # Claim sets of different lengths, so the base64 padding the decoder restores varies (0, 1 or 2 "=").
    @pytest.mark.parametrize(
        "claims",
        [{"id": 1}, {"id": 1, "username": "emilys"}, {"id": 12, "username": "ab", "iat": 1, "exp": 3601}],
    )
    def test_decode_returns_the_claims(self, claims):
        AssertHelper.assert_equals(decode_jwt_payload(_make_token(claims)), claims)

    def test_decode_handles_url_safe_characters(self):
        claims = {"note": "??>>~~"}  # encodes to "-" / "_" in base64url
        AssertHelper.assert_equals(decode_jwt_payload(_make_token(claims)), claims)

    @pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b", "a.b.c.d"])
    def test_decode_rejects_non_jwts(self, token):
        with pytest.raises(ValueError, match="Not a JWT"):
            decode_jwt_payload(token)

    def test_tamper_changes_only_the_signature(self):
        token = _make_token({"id": 1})
        forged = tamper_signature(token)
        AssertHelper.assert_not_equal(forged, token, "the forged token ")
        AssertHelper.assert_equals(forged.split(".")[:2], token.split(".")[:2], "header and claims ")
        AssertHelper.assert_equals(len(forged), len(token), "token length ")
        AssertHelper.assert_equals(decode_jwt_payload(forged), {"id": 1}, "claims of the forged token ")

    @pytest.mark.parametrize("last", ["A", "B", "z"])
    def test_tamper_always_changes_the_last_character(self, last):
        token = _make_token({"id": 1}, signature=f"sig{last}")
        AssertHelper.assert_not_equal(tamper_signature(token)[-1], last, "the last character ")
