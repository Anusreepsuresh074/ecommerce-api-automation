import allure
import pytest

from src.core.assert_helper import AssertHelper

pytestmark = [pytest.mark.products, pytest.mark.regression]


def _ids(response) -> list[int]:
    return [product["id"] for product in response.json()["products"]]


@allure.feature("Products")
@allure.story("Search")
class TestSearchProducts:
    # case: TC-get-products-search-happy-results-match-term
    @pytest.mark.smoke
    @allure.title("Every search hit matches the term")
    def test_search_results_all_match_the_term(self, product_helper):
        """RULE-products-search-title-description. Verifies: every hit is relevant."""
        body = product_helper.search_products("phone", {"limit": 0}).json()
        AssertHelper.assert_greater(body["total"], 0, "hits for 'phone' ")
        for product in body["products"]:
            text = f"{product['title']} {product['description']}".lower()
            AssertHelper.assert_contains(text, "phone", f"product {product['id']} title/description ")

    # case: TC-get-products-search-happy-case-insensitive
    @allure.title("Search ignores case")
    def test_search_is_case_insensitive(self, product_helper):
        """RULE-products-search-title-description. Verifies: case doesn't matter."""
        lower = _ids(product_helper.search_products("phone", {"limit": 0}))
        upper = _ids(product_helper.search_products("PHONE", {"limit": 0}))
        AssertHelper.assert_equals(upper, lower, "ids for PHONE vs phone ")

    # case: TC-get-products-search-negative-no-match-empty
    @allure.title("No match returns an empty result")
    def test_search_with_no_match_returns_empty(self, product_helper):
        """RULE-products-search-title-description. Verifies: no match is an empty result, not an error."""
        body = product_helper.search_products("qa-zzqqxx-no-such-product").json()
        AssertHelper.assert_field_equals(body, "products", [])
        AssertHelper.assert_field_equals(body, "total", 0)

    # case: TC-get-products-search-boundary-empty-query-returns-all
    @allure.title("Empty query returns the whole catalog")
    def test_empty_search_query_returns_whole_catalog(self, product_helper):
        """RULE-products-search-title-description (observed live: empty q → all).
        Verifies: pins the observed empty-q behaviour."""
        catalog_total = product_helper.list_products({"limit": 1}).json()["total"]
        AssertHelper.assert_field_equals(product_helper.search_products("").json(), "total", catalog_total)

    # case: TC-get-products-search-happy-paginated-results
    @allure.title("Search results can be paginated")
    def test_search_results_can_be_paginated(self, product_helper):
        """RULE-products-search-title-description + RULE-products-limit-skip-paginate.
        Verifies: search results page like the list."""
        full = _ids(product_helper.search_products("phone", {"limit": 0}))
        page = _ids(product_helper.search_products("phone", {"limit": 5, "skip": 5}))
        AssertHelper.assert_equals(page, full[5:10], "second page of results ")
