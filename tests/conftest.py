import os

import pytest

from src.core.api_base import ApiBase
from src.helper.auth_helper import AuthHelper
from src.helper.product_helper import ProductHelper

# Shared fixtures. Auth follows context/api-auth.md: log in once per session (per xdist worker),
# keep the tokens in memory only, and send the access token as `Authorization: Bearer`.


@pytest.fixture(scope="session")
def api_base(config):
    return ApiBase(config)


@pytest.fixture(scope="session")
def auth_helper(api_base):
    return AuthHelper(api_base)


@pytest.fixture(scope="session")
def product_helper(api_base):
    return ProductHelper(api_base)


@pytest.fixture(scope="session")
def auth_credentials():
    """One of DummyJSON's published test users, from the environment (.env locally, secrets in CI)."""
    missing = [name for name in ("AUTH_USERNAME", "AUTH_PASSWORD") if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Set {', '.join(missing)} (see .env.example) to run the authenticated tests")
    return {"username": os.environ["AUTH_USERNAME"], "password": os.environ["AUTH_PASSWORD"]}


@pytest.fixture(scope="session")
def session_tokens(auth_helper, auth_credentials):
    body = auth_helper.login(**auth_credentials).json()
    return {"access": body["accessToken"], "refresh": body["refreshToken"]}


@pytest.fixture(scope="session")
def bearer_header(session_tokens):
    return AuthHelper.bearer_header(session_tokens["access"])
