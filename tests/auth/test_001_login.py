import allure
import pytest

from src.core.assert_helper import AssertHelper
from src.schema.auth_schema import JWT_CLAIMS_SCHEMA
from src.schema.error_schema import ERROR_SCHEMA
from src.utils.jwt_utils import decode_jwt_payload
from tests.auth.auth_td import AuthTestData

pytestmark = [pytest.mark.auth, pytest.mark.regression]


@allure.feature("Auth")
@allure.story("Login")
class TestLogin:
    # case: TC-post-auth-login-happy-valid-credentials
    @pytest.mark.smoke
    @allure.title("Valid credentials return a token pair")
    def test_login_with_valid_credentials_returns_token_pair(self, auth_helper, auth_credentials):
        """RULE-auth-login-returns-token-pair: login returns identity + access and refresh JWTs.
        Verifies: valid credentials log the user in."""
        body = auth_helper.login(**auth_credentials).json()
        AssertHelper.assert_field_equals(body, "username", auth_credentials["username"])
        AssertHelper.assert_not_equal(body["accessToken"], body["refreshToken"], "access token vs refresh token ")

    # case: TC-post-auth-login-contract-schema-login-response-shape
    @allure.title("Login response matches LoginResponse exactly")
    def test_login_response_matches_schema(self, auth_helper, auth_credentials):
        """RULE-auth-login-returns-token-pair. Verifies: the login body has exactly the documented fields."""
        auth_helper.login(**auth_credentials)  # the helper validates LOGIN_RESPONSE_SCHEMA (strict, JWT-shaped)

    # case: TC-post-auth-login-contract-schema-jwt-claims-identify-user
    @allure.title("Access token claims identify the user")
    def test_access_token_claims_identify_the_user(self, auth_helper, auth_credentials):
        """RULE-auth-login-returns-token-pair. Verifies: the token itself names the logged-in user."""
        body = auth_helper.login(**auth_credentials).json()
        claims = decode_jwt_payload(body["accessToken"])
        AssertHelper.assert_schema(claims, JWT_CLAIMS_SCHEMA)
        AssertHelper.assert_field_equals(claims, "id", body["id"])
        AssertHelper.assert_field_equals(claims, "username", body["username"])

    # case: TC-post-auth-login-happy-sets-token-cookies
    @allure.title("Login sets both token cookies")
    def test_login_sets_access_and_refresh_cookies(self, auth_helper, auth_credentials):
        """RULE-auth-login-sets-token-cookies: tokens are returned in the body and set as cookies.
        Verifies: browser clients get the tokens as cookies."""
        cookies = auth_helper.login(**auth_credentials).cookies.keys()
        AssertHelper.assert_contains(cookies, "accessToken", "Set-Cookie names ")
        AssertHelper.assert_contains(cookies, "refreshToken", "Set-Cookie names ")

    # case: TC-post-auth-login-happy-default-lifetime-60-min
    @allure.title("Token lifetime defaults to 60 minutes")
    def test_token_lifetime_defaults_to_60_minutes(self, auth_helper, auth_credentials):
        """RULE-auth-expiry-configurable: expiresInMins optional, default 60, max 43200.
        Verifies: no expiresInMins gives the documented default."""
        claims = decode_jwt_payload(auth_helper.login(**auth_credentials).json()["accessToken"])
        AssertHelper.assert_equals(claims["exp"] - claims["iat"], 3600, "token lifetime in seconds ")

    # case: TC-post-auth-login-boundary-expires-in-mins-min-and-max
    @pytest.mark.parametrize("minutes", AuthTestData.LIFETIME_BOUNDS_MINUTES)
    @allure.title("Token lifetime follows expiresInMins")
    def test_token_lifetime_follows_expires_in_mins(self, auth_helper, auth_credentials, minutes):
        """RULE-auth-expiry-configurable. Verifies: the requested lifetime is honoured at both ends."""
        body = auth_helper.login(**auth_credentials, expires_in_mins=minutes).json()
        claims = decode_jwt_payload(body["accessToken"])
        AssertHelper.assert_equals(claims["exp"] - claims["iat"], minutes * 60, "token lifetime in seconds ")

    # case: TC-post-auth-login-boundary-expires-in-mins-zero
    @allure.title("expiresInMins 0 gives a 30-day token")
    def test_expires_in_mins_zero_gives_30_day_token(self, auth_helper, auth_credentials):
        """RULE-auth-expiry-configurable (observed live: 0 → 30 days). Verifies: pins the observed meaning of 0."""
        claims = decode_jwt_payload(auth_helper.login(**auth_credentials, expires_in_mins=0).json()["accessToken"])
        AssertHelper.assert_equals(claims["exp"] - claims["iat"], 2592000, "token lifetime in seconds ")

    # case: TC-post-auth-login-boundary-expires-in-mins-above-max
    @pytest.mark.xfail(reason="Known API defect: expiresInMins 43201 returns 500, not 400", strict=True)
    @allure.title("Lifetime above the maximum is rejected with 400")
    def test_login_rejects_lifetime_above_maximum(self, auth_helper, auth_credentials):
        """RULE-auth-expiry-configurable. Verifies: one over the max is a client error."""
        auth_helper.login(
            **auth_credentials,
            expires_in_mins=43201,
            status_code=400,
            message="Maximum access token expire time can be 43200 minutes",
        )

    # case: TC-post-auth-login-boundary-expires-in-mins-negative
    @pytest.mark.xfail(reason="Known API defect: expiresInMins -1 returns 500 (with a misleading message)", strict=True)
    @allure.title("Negative lifetime is rejected with 400")
    def test_login_rejects_negative_lifetime(self, auth_helper, auth_credentials):
        """RULE-auth-expiry-configurable. Verifies: a negative lifetime is a client error."""
        auth_helper.login(**auth_credentials, expires_in_mins=-1, status_code=400)

    # case: TC-post-auth-login-negative-bad-credentials-same-message
    @pytest.mark.parametrize("username,password", AuthTestData.BAD_CREDENTIALS)
    @allure.title("Bad credentials are rejected without saying which")
    def test_login_rejects_bad_credentials_without_saying_which(
        self, auth_helper, auth_credentials, username, password
    ):
        """RULE-auth-bad-credentials-generic-error: wrong password and unknown user both return 400
        "Invalid credentials". Verifies: no login, and no hint which usernames exist."""
        username = username.format(user=auth_credentials["username"])
        auth_helper.login(username, password, status_code=400, message="Invalid credentials")

    # case: TC-post-auth-login-negative-missing-credentials
    @pytest.mark.parametrize("send_username,send_password", AuthTestData.MISSING_CREDENTIAL_FIELDS)
    @allure.title("Username and password are both required")
    def test_login_requires_username_and_password(self, auth_helper, auth_credentials, send_username, send_password):
        """RULE-auth-login-requires-credentials: missing username/password → 400.
        Verifies: required fields are enforced."""
        auth_helper.login(
            auth_credentials["username"] if send_username else None,
            auth_credentials["password"] if send_password else None,
            status_code=400,
            message="Username and password required",
        )

    # case: TC-post-auth-login-error-shape-login-error-body
    @allure.title("Login errors use the standard error body")
    def test_login_errors_use_standard_error_shape(self, auth_helper, auth_credentials):
        """Endpoint inventory: every error body is exactly {"message": <string>}.
        Verifies: every login error is the standard {message} body."""
        wrong_password = auth_helper.login(auth_credentials["username"], "not-the-password", status_code=400)
        missing_fields = auth_helper.login(status_code=400)
        for response in (wrong_password, missing_fields):
            AssertHelper.assert_schema(response.json(), ERROR_SCHEMA)
