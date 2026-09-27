from src.constants.endpoints.auth_ep import CURRENT_USER, LOGIN, REFRESH
from src.core.assert_helper import AssertHelper
from src.payload.auth_payload import login_payload, refresh_payload
from src.schema.auth_schema import CURRENT_USER_SCHEMA, LOGIN_RESPONSE_SCHEMA, REFRESH_RESPONSE_SCHEMA
from src.utils.reporting import step


class AuthHelper:
    def __init__(self, api_base):
        self.api_base = api_base

    @staticmethod
    def bearer_header(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    @step("Log in")
    def login(self, username=None, password=None, expires_in_mins=None, status_code: int = 200, message=None):
        response = self.api_base.post(LOGIN, json=login_payload(username, password, expires_in_mins))
        return AssertHelper.assert_response(response, status_code, LOGIN_RESPONSE_SCHEMA, message)

    @step("Get the current user")
    def get_current_user(self, headers=None, cookies=None, status_code: int = 200, message=None):
        response = self.api_base.get(CURRENT_USER, headers=headers, cookies=cookies)
        return AssertHelper.assert_response(response, status_code, CURRENT_USER_SCHEMA, message)

    @step("Refresh tokens")
    def refresh(self, refresh_token=None, expires_in_mins=None, cookies=None, status_code: int = 200, message=None):
        response = self.api_base.post(REFRESH, json=refresh_payload(refresh_token, expires_in_mins), cookies=cookies)
        return AssertHelper.assert_response(response, status_code, REFRESH_RESPONSE_SCHEMA, message)
