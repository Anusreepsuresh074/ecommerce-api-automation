import pytest


class ProductsTestData:
    # TC-get-products-negative-invalid-limit
    INVALID_LIMITS = [pytest.param("-5", id="negative"), pytest.param("abc", id="not-a-number")]

    # TC-get-products-happy-select-fields: the two documented select forms.
    SELECT_FORMS = [
        pytest.param({"select": "title,price"}, id="comma-separated"),
        pytest.param({"select": ["title", "price"]}, id="repeated-param"),
    ]

    SORT_ORDERS = [pytest.param("asc", id="asc"), pytest.param("desc", id="desc")]

    # TC-get-products-happy-modified-date-filter: which bound(s) to apply.
    DATE_FILTER_BOUNDS = [
        pytest.param(True, False, id="modified-after"),
        pytest.param(False, True, id="modified-before"),
        pytest.param(True, True, id="both"),
    ]

    # TC-get-products-boundary-delay-limit: the documented max, and one over it ([Assumption] cut-off).
    DELAYS = [pytest.param(5000, 200, id="max-5000"), pytest.param(5001, 400, id="over-max-5001")]

    # TC-get-products-id-negative-unknown-id
    UNKNOWN_IDS = [
        pytest.param("99999", id="unknown"),
        pytest.param("abc", id="non-numeric"),
        pytest.param("0", id="zero"),
    ]

    UPDATE_METHODS = [pytest.param("PUT", id="put"), pytest.param("PATCH", id="patch")]
    WRITE_METHODS = [
        pytest.param("PUT", id="put"),
        pytest.param("PATCH", id="patch"),
        pytest.param("DELETE", id="delete"),
    ]
    PROTECTED_WRITE_METHODS = [pytest.param("PUT", id="put"), pytest.param("DELETE", id="delete")]
