def login_payload(username: str | None = None, password: str | None = None, expires_in_mins: int | None = None) -> dict:
    """Login body. A field passed as None is left out, so the same factory builds the missing-field cases."""
    payload = {}
    if username is not None:
        payload["username"] = username
    if password is not None:
        payload["password"] = password
    if expires_in_mins is not None:
        payload["expiresInMins"] = expires_in_mins
    return payload


def refresh_payload(refresh_token: str | None = None, expires_in_mins: int | None = None) -> dict:
    """Refresh body. refresh_token=None leaves it out (the cookie-only and missing-token cases)."""
    payload = {}
    if refresh_token is not None:
        payload["refreshToken"] = refresh_token
    if expires_in_mins is not None:
        payload["expiresInMins"] = expires_in_mins
    return payload
