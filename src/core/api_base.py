import http.cookiejar

import allure
import requests

from src.utils.logger import get_logger
from src.utils.redaction import redact, redact_headers, safe_body
from src.utils.reporting import step

logger = get_logger(__name__)


class _NoCookieJarPolicy(http.cookiejar.DefaultCookiePolicy):
    """Never store Set-Cookie: login sets token cookies, and a stored one would silently authenticate
    later calls that are meant to be anonymous (the missing-token tests)."""

    def set_ok(self, cookie, request):
        return False


class ApiBase:
    """Every HTTP call in this framework goes through here — never raw requests in tests or helpers."""

    def __init__(self, config):
        self.base_url = config.base_url
        self.timeout = config.timeout
        # One session per ApiBase (per test worker): connections are reused instead of a new TCP +
        # TLS handshake on every call. No cookies persist between calls — tests pass them explicitly.
        self.session = requests.Session()
        self.session.cookies.set_policy(_NoCookieJarPolicy())

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @step("{method} {path}")
    def _request(self, method: str, path: str, headers=None, params=None, json=None, **kwargs):
        url = self._url(path)
        safe_headers, safe_json = redact_headers(headers), redact(json)
        logger.info("%s %s | params=%s | headers=%s | json=%s", method, url, params, safe_headers, safe_json)
        self._attach("Request", f"{method} {url}\nparams={params}\nheaders={safe_headers}\njson={safe_json}")
        response = self.session.request(
            method=method, url=url, headers=headers, params=params, json=json, timeout=self.timeout, **kwargs
        )
        body = safe_body(response)
        logger.info("-> %s %s", response.status_code, body)
        self._attach("Response", f"status_code={response.status_code}\n{body}")
        return response

    @staticmethod
    def _attach(name: str, body: str) -> None:
        allure.attach(body, name=name, attachment_type=allure.attachment_type.TEXT)

    def get(self, path: str, headers=None, params=None, **kwargs):
        return self._request("GET", path, headers=headers, params=params, **kwargs)

    def post(self, path: str, headers=None, json=None, params=None, **kwargs):
        return self._request("POST", path, headers=headers, json=json, params=params, **kwargs)

    def put(self, path: str, headers=None, json=None, params=None, **kwargs):
        return self._request("PUT", path, headers=headers, json=json, params=params, **kwargs)

    def patch(self, path: str, headers=None, json=None, params=None, **kwargs):
        return self._request("PATCH", path, headers=headers, json=json, params=params, **kwargs)

    def delete(self, path: str, headers=None, params=None, **kwargs):
        return self._request("DELETE", path, headers=headers, params=params, **kwargs)
