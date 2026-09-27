import allure
import pytest

from src.core.assert_helper import AssertHelper
from src.helper.auth_helper import AuthHelper
from src.schema.auth_schema import REFRESH_RESPONSE_SCHEMA
from src.schema.error_schema import ERROR_SCHEMA
from src.utils.jwt_utils import decode_jwt_payload

pytestmark = [pytest.mark.auth, pytest.mark.regression]


@allure.feature("Auth")
@allure.story("Refresh tokens")
class TestRefresh:
    # case: TC-post-auth-refresh-happy-refresh-token-in-body
    @pytest.mark.smoke
    @allure.title("Refresh issues a working access token")
    def test_refresh_issues_working_new_tokens(self, auth_helper, session_tokens):
        """RULE-auth-refresh-issues-new-pair: new pair without username/password; token in body or cookie.
        Verifies: a refresh token buys a working access token."""
        new_access = auth_helper.refresh(session_tokens["refresh"]).json()["accessToken"]
        auth_helper.get_current_user(headers=AuthHelper.bearer_header(new_access))

    # case: TC-post-auth-refresh-happy-refresh-token-in-cookie
    @allure.title("Refresh accepts the refreshToken cookie")
    def test_refresh_accepts_refresh_token_cookie(self, auth_helper, session_tokens):
        """RULE-auth-refresh-issues-new-pair. Verifies: the cookie path works (docs)."""
        auth_helper.refresh(cookies={"refreshToken": session_tokens["refresh"]})

    # case: TC-post-auth-refresh-boundary-refresh-expires-in-mins
    @allure.title("Refresh honours expiresInMins for the new access token")
    def test_refresh_honours_expires_in_mins(self, auth_helper, session_tokens):
        """RULE-auth-expiry-configurable (docs: refresh expiresInMins applies to the access token).
        Verifies: the new access token gets the requested lifetime."""
        claims = decode_jwt_payload(
            auth_helper.refresh(session_tokens["refresh"], expires_in_mins=5).json()["accessToken"]
        )
        AssertHelper.assert_equals(claims["exp"] - claims["iat"], 300, "new access token lifetime in seconds ")

    # case: TC-post-auth-refresh-contract-schema-refresh-response-shape
    @allure.title("Refresh response matches RefreshResponse exactly")
    def test_refresh_response_matches_schema(self, auth_helper, session_tokens):
        """RULE-auth-refresh-issues-new-pair. Verifies: refresh returns exactly the two tokens."""
        AssertHelper.assert_schema(auth_helper.refresh(session_tokens["refresh"]).json(), REFRESH_RESPONSE_SCHEMA)

    # case: TC-post-auth-refresh-negative-invalid-refresh-token
    @allure.title("Invalid refresh token is rejected with 403")
    def test_invalid_refresh_token_is_rejected_with_403(self, auth_helper):
        """RULE-auth-refresh-token-required: invalid → 403, missing → 401. Verifies: a bad refresh token is refused."""
        auth_helper.refresh("not-a-token", status_code=403, message="Invalid refresh token")

    # case: TC-post-auth-refresh-negative-missing-refresh-token
    @allure.title("Missing refresh token is rejected with 401")
    def test_missing_refresh_token_is_rejected_with_401(self, auth_helper):
        """RULE-auth-refresh-token-required. Verifies: the refresh token is required."""
        auth_helper.refresh(status_code=401, message="Refresh token required")

    # case: TC-post-auth-refresh-auth-authz-access-token-as-refresh
    @pytest.mark.xfail(
        reason="Known API defect (security): an access token is accepted as a refresh token", strict=True
    )
    @allure.title("Access token cannot be used as a refresh token")
    def test_access_token_cannot_be_used_as_refresh_token(self, auth_helper, session_tokens):
        """RULE-auth-token-types-not-interchangeable (inferred). Verifies: tokens can't be swapped (other direction)."""
        auth_helper.refresh(session_tokens["access"], status_code=403, message="Invalid refresh token")

    # case: TC-post-auth-refresh-auth-authz-used-refresh-token-reused
    @pytest.mark.xfail(
        reason="Known API defect (security): a used refresh token is accepted again (no rotation)", strict=True
    )
    @allure.title("A used refresh token cannot be reused")
    def test_used_refresh_token_cannot_be_reused(self, auth_helper, auth_credentials):
        """RULE-auth-refresh-token-single-use (inferred). Verifies: a refresh token is single-use."""
        refresh = auth_helper.login(**auth_credentials).json()["refreshToken"]
        auth_helper.refresh(refresh)
        auth_helper.refresh(refresh, status_code=403, message="Invalid refresh token")

    # case: TC-post-auth-refresh-error-shape-refresh-error-body
    @allure.title("Refresh errors use the standard error body")
    def test_refresh_errors_use_standard_error_shape(self, auth_helper):
        """Endpoint inventory: every error body is exactly {"message": <string>}.
        Verifies: refresh errors use the standard body."""
        for response in (auth_helper.refresh("not-a-token", status_code=403), auth_helper.refresh(status_code=401)):
            AssertHelper.assert_schema(response.json(), ERROR_SCHEMA)
