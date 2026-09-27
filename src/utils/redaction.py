import json

# Credentials are masked before anything is logged, attached to the report, or put in a failure
# message. Any field whose name contains one of these words, and these headers, count as credentials.
_SENSITIVE_KEY_PARTS = ("password", "token", "secret")
_SENSITIVE_HEADERS = {"authorization", "cookie"}


def is_sensitive_key(key: str) -> bool:
    return any(part in key.lower() for part in _SENSITIVE_KEY_PARTS)


def redact(value):
    if isinstance(value, dict):
        return {key: "***" if is_sensitive_key(key) else redact(val) for key, val in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def redact_headers(headers):
    if not headers:
        return headers
    return {key: ("***" if key.lower() in _SENSITIVE_HEADERS else val) for key, val in headers.items()}


def safe_body(response, limit: int = 500) -> str:
    """A response body for logs and failure messages, with credential fields masked."""
    try:
        return json.dumps(redact(response.json()))[:limit]
    except ValueError:
        return response.text[:limit]
