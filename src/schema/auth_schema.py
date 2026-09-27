JWT = {"type": "string", "pattern": r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"}

# docs/auth "Login user and get tokens" example output — exactly these fields.
LOGIN_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "username": {"type": "string"},
        "email": {"type": "string"},
        "firstName": {"type": "string"},
        "lastName": {"type": "string"},
        "gender": {"type": "string"},
        "image": {"type": "string"},
        "accessToken": JWT,
        "refreshToken": JWT,
    },
    "required": ["id", "username", "email", "firstName", "lastName", "gender", "image", "accessToken", "refreshToken"],
    "additionalProperties": False,
}

# docs/auth "Refresh auth session" example output.
REFRESH_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {"accessToken": JWT, "refreshToken": JWT},
    "required": ["accessToken", "refreshToken"],
    "additionalProperties": False,
}

# docs/auth "Get current auth user" example: the identity fields, then "... // other user fields".
CURRENT_USER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "username": {"type": "string"},
        "email": {"type": "string"},
        "firstName": {"type": "string"},
        "lastName": {"type": "string"},
        "gender": {"type": "string"},
        "image": {"type": "string"},
    },
    "required": ["id", "username", "email", "firstName", "lastName"],
}

# Decoded access-token payload (context/api-auth.md → Response validation).
JWT_CLAIMS_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "username": {"type": "string"},
        "iat": {"type": "integer"},
        "exp": {"type": "integer"},
    },
    "required": ["id", "username", "iat", "exp"],
}
