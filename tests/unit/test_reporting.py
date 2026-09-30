import contextlib

import pytest

from src.core.assert_helper import AssertHelper
from src.utils import reporting
from src.utils.reporting import step

pytestmark = pytest.mark.unit


@pytest.fixture
def recorded_steps(monkeypatch):
    """Replaces allure.step with a recorder of every argument it is called with."""
    calls = []

    @contextlib.contextmanager
    def fake_step(*args, **kwargs):
        calls.append((args, kwargs))
        yield

    monkeypatch.setattr(reporting.allure, "step", fake_step)
    return calls


class TestStep:
    def test_title_is_formatted_from_the_arguments(self, recorded_steps):
        @step("{method} {path}")
        def call(method, path, headers=None):
            return "response"

        AssertHelper.assert_equals(call("GET", "/auth/me", headers={"Authorization": "Bearer a.b.c"}), "response")
        AssertHelper.assert_equals(recorded_steps, [(("GET /auth/me",), {})], "allure.step calls ")

    def test_only_the_title_reaches_allure(self, recorded_steps):
        @step("Log in")
        def login(username, password):
            return username

        login("emilys", password="hunter2")
        AssertHelper.assert_equals(recorded_steps, [(("Log in",), {})], "allure.step calls ")

    def test_defaults_can_be_used_in_the_title(self, recorded_steps):
        @step("Get product {product_id}")
        def get_product(product_id=1):
            return product_id

        get_product()
        AssertHelper.assert_equals(recorded_steps, [(("Get product 1",), {})], "allure.step calls ")

    def test_exceptions_propagate(self, recorded_steps):
        @step("Fails")
        def fails():
            raise AssertionError("boom")

        with pytest.raises(AssertionError, match="boom"):
            fails()

    def test_wrapped_function_keeps_its_name_and_docstring(self):
        @step("Documented")
        def documented():
            """Docstring."""

        AssertHelper.assert_equals(documented.__name__, "documented")
        AssertHelper.assert_equals(documented.__doc__, "Docstring.")
