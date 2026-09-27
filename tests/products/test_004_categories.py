import allure
import pytest

from src.core.assert_helper import AssertHelper
from src.utils.date_utils import parse_iso, pivot_between

pytestmark = [pytest.mark.products, pytest.mark.regression]


@allure.feature("Products")
@allure.story("Categories")
class TestCategories:
    # case: TC-get-products-categories-contract-schema-category-lists-agree
    @allure.title("The two category routes agree")
    def test_category_routes_agree(self, product_helper):
        """RULE-products-categories-lists-agree. Verifies: the two category routes list the same categories."""
        categories = product_helper.list_categories().json()  # CATEGORY_LIST_SCHEMA in the helper
        slugs = product_helper.list_category_slugs().json()
        AssertHelper.assert_equals([category["slug"] for category in categories], slugs, "category slugs ")

    # case: TC-get-products-category-slug-happy-filter-only-that-category
    @allure.title("Category filter returns only that category")
    def test_category_filter_returns_only_that_category(self, product_helper):
        """RULE-products-category-filter. Verifies: the filter is exact."""
        body = product_helper.list_by_category("smartphones", {"limit": 0}).json()
        AssertHelper.assert_greater(body["total"], 0, "smartphones ")
        for product in body["products"]:
            AssertHelper.assert_field_equals(product, "category", "smartphones")

    # case: TC-get-products-category-slug-negative-unknown-category-empty
    @allure.title("Unknown category returns an empty list")
    def test_unknown_category_returns_empty_list(self, product_helper):
        """RULE-products-category-filter. Verifies: an unknown category is empty, not 404."""
        body = product_helper.list_by_category("no-such-category").json()
        AssertHelper.assert_field_equals(body, "products", [])
        AssertHelper.assert_field_equals(body, "total", 0)

    # case: TC-get-products-category-slug-happy-combined-with-date-filter
    @allure.title("Category filter combines with the date filter")
    def test_category_filter_combines_with_date_filter(self, product_helper):
        """RULE-products-modified-date-filter + RULE-products-category-filter.
        Verifies: filters combine as documented."""
        category = product_helper.list_by_category("smartphones", {"limit": 0, "select": "meta"}).json()["products"]
        after = pivot_between([product["meta"]["updatedAt"] for product in category], 0.5)
        expected = [p["id"] for p in category if parse_iso(p["meta"]["updatedAt"]) > parse_iso(after)]
        filtered = product_helper.list_by_category(
            "smartphones", {"limit": 0, "select": "meta", "modifiedAfter": after}
        )
        AssertHelper.assert_equals(
            sorted(p["id"] for p in filtered.json()["products"]), sorted(expected), "filtered ids "
        )
