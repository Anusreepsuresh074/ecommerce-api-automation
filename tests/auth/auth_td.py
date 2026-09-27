import pytest


class AuthTestData:
    # TC-post-auth-login-boundary-expires-in-mins-min-and-max: the two ends of the documented range.
    LIFETIME_BOUNDS_MINUTES = [
        pytest.param(1, id="min-1"),
        pytest.param(43200, id="max-43200"),
    ]

    # TC-post-auth-login-negative-bad-credentials-same-message. "{user}" = the configured username.
    BAD_CREDENTIALS = [
        pytest.param("{user}", "not-the-password", id="wrong-password"),
        pytest.param("qa_no_such_user", "whatever", id="unknown-username"),
    ]

    # TC-post-auth-login-negative-missing-credentials: which of the two fields to send.
    MISSING_CREDENTIAL_FIELDS = [
        pytest.param(False, False, id="empty-body"),
        pytest.param(True, False, id="username-only"),
        pytest.param(False, True, id="password-only"),
    ]
