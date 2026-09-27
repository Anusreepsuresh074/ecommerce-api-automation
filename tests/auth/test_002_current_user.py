import time

import allure
import pytest

from src.core.assert_helper import AssertHelper
from src.helper.auth_helper import AuthHelper
from src.schema.auth_schema import CURRENT_USER_SCHEMA
from src.schema.error_schema import ERROR_SCHEMA
from src.utils.jwt_utils import decode_jwt_payload, tamper_signature

pytestmark = [pytest.mark.auth, pytest.mark.regression]


@allure.feature("Auth")
@allure.story("Current user (Bearer access)")
class TestCurrentUser:
    # case: TC-get-auth-me-happy-valid-bearer
    @pytest.mark.smoke
    @allure.title("Valid Bearer token returns the current user")
    def test_valid_bearer_token_returns_current_user(self, auth_helper, bearer_header, auth_credentials):
        """RULE-auth-bearer-required-on-auth-routes: /auth/* take Authorization: Bearer <token>.
        Verifies: a valid token identifies its user."""
        body = auth_helper.get_current_user(headers=bearer_header).json()
        AssertHelper.assert_field_equals(body, "username", auth_credentials["username"])

    # case: TC-get-auth-me-happy-cookie-token
    @allure.title("Access token is accepted as a cookie")
    def test_access_token_accepted_as_cookie(self, auth_helper, session_tokens, auth_credentials):
        """RULE-auth-cookie-token-accepted. Verifies: the cookie path works like the header."""
        body = auth_helper.get_current_user(cookies={"accessToken": session_tokens["access"]}).json()
        AssertHelper.assert_field_equals(body, "username", auth_credentials["username"])

    # case: TC-get-auth-me-contract-schema-current-user-shape
    @allure.title("Current user matches CurrentUser")
    def test_current_user_response_matches_schema(self, auth_helper, bearer_header):
        """Endpoint inventory: CurrentUser (identity fields + other user fields).
        Verifies: identity fields a client relies on are present and typed."""
        AssertHelper.assert_schema(auth_helper.get_current_user(headers=bearer_header).json(), CURRENT_USER_SCHEMA)

    # case: TC-get-auth-me-auth-authz-missing-token
    @pytest.mark.smoke
    @allure.title("Missing token is rejected with 401")
    def test_missing_token_is_rejected_with_401(self, auth_helper):
        """RULE-auth-bearer-required-on-auth-routes. Verifies: no token, no access."""
        auth_helper.get_current_user(status_code=401, message="Access Token is required")

    # case: TC-get-auth-me-auth-authz-expired-token-then-refresh
    @pytest.mark.slow
    @allure.title("Expired token is rejected, then refresh recovers")
    def test_expired_token_rejected_then_refresh_recovers(self, auth_helper, auth_credentials):
        """RULE-auth-expired-token-rejected + RULE-auth-refresh-issues-new-pair.
        Verifies: the full lifecycle — works → expires → refresh recovers."""
        body = auth_helper.login(**auth_credentials, expires_in_mins=1).json()
        access, refresh = body["accessToken"], body["refreshToken"]
        auth_helper.get_current_user(headers=AuthHelper.bearer_header(access))

        time.sleep(max(0, decode_jwt_payload(access)["exp"] - time.time()) + 5)  # the one justified wait: real expiry

        auth_helper.get_current_user(
            headers=AuthHelper.bearer_header(access), status_code=401, message="Token Expired!"
        )
        new_access = auth_helper.refresh(refresh).json()["accessToken"]
        auth_helper.get_current_user(headers=AuthHelper.bearer_header(new_access))

    # case: TC-get-auth-me-auth-authz-malformed-token
    @pytest.mark.xfail(reason="Known API defect: a malformed token returns 500 'invalid token', not 401", strict=True)
    @allure.title("Malformed token is rejected with 401")
    def test_malformed_token_is_rejected_with_401(self, auth_helper):
        """RULE-auth-invalid-token-rejected (inferred). Verifies: garbage is refused cleanly."""
        auth_helper.get_current_user(headers=AuthHelper.bearer_header("abc.def.ghi"), status_code=401)

    # case: TC-get-auth-me-auth-authz-forged-signature
    @pytest.mark.xfail(
        reason="Known API defect: a forged signature returns 500 'invalid signature', not 401", strict=True
    )
    @allure.title("Forged signature is rejected with 401")
    def test_forged_signature_is_rejected_with_401(self, auth_helper, session_tokens):
        """RULE-auth-invalid-token-rejected (inferred). Verifies: a forged signature is refused."""
        forged = tamper_signature(session_tokens["access"])
        auth_helper.get_current_user(headers=AuthHelper.bearer_header(forged), status_code=401)

    # case: TC-get-auth-me-auth-authz-wrong-auth-scheme
    @pytest.mark.xfail(reason="Known API defect: 'Authorization: Basic <token>' returns 500, not 401", strict=True)
    @allure.title("Wrong auth scheme is rejected with 401")
    def test_wrong_auth_scheme_is_rejected_with_401(self, auth_helper, session_tokens):
        """RULE-auth-invalid-token-rejected (inferred). Verifies: a non-Bearer scheme is refused."""
        auth_helper.get_current_user(headers={"Authorization": f"Basic {session_tokens['access']}"}, status_code=401)

    # case: TC-get-auth-me-auth-authz-missing-bearer-prefix
    @pytest.mark.xfail(reason="Known API defect: a raw token without 'Bearer ' is accepted (200)", strict=True)
    @allure.title("Token without the Bearer prefix is rejected")
    def test_token_without_bearer_prefix_is_rejected(self, auth_helper, session_tokens):
        """RULE-auth-invalid-token-rejected (inferred). Verifies: the documented header format is enforced."""
        auth_helper.get_current_user(headers={"Authorization": session_tokens["access"]}, status_code=401)

    # case: TC-get-auth-me-auth-authz-refresh-token-as-access
    @pytest.mark.xfail(
        reason="Known API defect (security): a refresh token is accepted as an access token", strict=True
    )
    @allure.title("Refresh token cannot be used as an access token")
    def test_refresh_token_cannot_be_used_as_access_token(self, auth_helper, session_tokens):
        """RULE-auth-token-types-not-interchangeable (inferred). Verifies: tokens can't be swapped."""
        auth_helper.get_current_user(headers=AuthHelper.bearer_header(session_tokens["refresh"]), status_code=401)

    # case: TC-get-auth-me-contract-schema-no-sensitive-fields
    @pytest.mark.xfail(
        reason="Known API defect (security): /auth/me returns password, ssn, ein, bank, crypto", strict=True
    )
    @allure.title("Current user response hides sensitive data")
    def test_current_user_response_hides_sensitive_data(self, auth_helper, bearer_header):
        """RULE-auth-me-hides-sensitive-fields (inferred). Verifies: no secrets in the identity response."""
        body = auth_helper.get_current_user(headers=bearer_header).json()
        for field in ("password", "ssn", "ein", "bank", "crypto"):
            AssertHelper.assert_field_absent(body, field, "/auth/me.")

    # case: TC-get-auth-me-error-shape-me-error-body
    @allure.title("Protected-route errors use the standard error body")
    def test_protected_route_errors_use_standard_error_shape(self, auth_helper):
        """Endpoint inventory: every error body is exactly {"message": <string>}.
        Verifies: auth errors use the standard {message} body."""
        AssertHelper.assert_schema(auth_helper.get_current_user(status_code=401).json(), ERROR_SCHEMA)
