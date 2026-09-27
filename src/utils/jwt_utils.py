import base64
import json


def decode_jwt_payload(token: str) -> dict:
    """Reads a JWT's claims. Decoding is not verification — anyone can read the claims; only the
    server can check the signature. Tests use it to see what the server put in the token."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError(f"Not a JWT: expected 3 dot-separated parts, got {len(parts)}")
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def tamper_signature(token: str) -> str:
    """Same header and claims, one signature character changed — a forged token."""
    last = token[-1]
    return token[:-1] + ("A" if last != "A" else "B")
