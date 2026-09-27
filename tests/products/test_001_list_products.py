import allure
import pytest

from src.core.assert_helper import AssertHelper
from src.schema.error_schema import ERROR_SCHEMA
from src.utils.date_utils import parse_iso, pivot_between
from tests.products.products_td import ProductsTestData

pytestmark = [pytest.mark.products, pytest.mark.regression]


@allure.feature("Products")
@allure.story("List: pagination, select, sort, date filter, delay")
class TestListProducts:
    # case: TC-get-products-happy-default-first-page-30
    @pytest.mark.smoke
    @allure.title("Default list is the first page of 30")
    def test_default_list_returns_first_page_of_30(self, product_helper):
        """RULE-products-default-page-30. Verifies: defaults: first page of 30."""
        body = product_helper.list_products().json()
        AssertHelper.assert_equals(len(body["products"]), 30, "products on the page ")
        AssertHelper.assert_field_equals(body, "skip", 0)
        AssertHelper.assert_field_equals(body, "limit", 30)
        AssertHelper.assert_greater_or_equal(body["total"], 30, "total ")

    # case: TC-get-products-contract-schema-product-list-shape
    @allure.title("Every product in the catalog matches Product")
    def test_product_list_matches_schema(self, product_helper):
        """Endpoint inventory: ProductList / Product (21 required fields, brand optional, no extras).
        Verifies: every item on a page is a valid Product."""
        product_helper.list_products({"limit": 0})  # the helper validates PRODUCT_LIST_SCHEMA over every item

    # case: TC-get-products-happy-limit-skip-window
    @allure.title("limit and skip select the right window")
    def test_limit_and_skip_select_the_right_window(self, product_helper):
        """RULE-products-limit-skip-paginate. Verifies: skip/limit pick the exact window."""
        AssertHelper.assert_equals(
            product_helper.product_ids(product_helper.list_products({"limit": 5, "skip": 10})), [11, 12, 13, 14, 15]
        )

    # case: TC-get-products-happy-pages-do-not-overlap
    @allure.title("Consecutive pages do not overlap")
    def test_consecutive_pages_do_not_overlap(self, product_helper):
        """RULE-products-limit-skip-paginate. Verifies: page 2 continues where page 1 ended."""
        page1 = product_helper.product_ids(product_helper.list_products({"limit": 10, "skip": 0}))
        page2 = product_helper.product_ids(product_helper.list_products({"limit": 10, "skip": 10}))
        AssertHelper.assert_equals(set(page1) & set(page2), set(), "ids on both pages ")
        AssertHelper.assert_equals(page2[0], page1[-1] + 1, "first id of page 2 ")

    # case: TC-get-products-boundary-limit-zero-returns-all
    @allure.title("limit=0 returns every product")
    def test_limit_zero_returns_every_product(self, product_helper):
        """RULE-products-limit-skip-paginate. Verifies: limit=0 means no limit."""
        body = product_helper.list_products({"limit": 0}).json()
        AssertHelper.assert_equals(len(body["products"]), body["total"], "products returned vs total ")

    # case: TC-get-products-boundary-skip-beyond-total
    @allure.title("Skipping past the end returns an empty page")
    def test_skip_past_the_end_returns_empty_page(self, product_helper):
        """RULE-products-limit-skip-paginate. Verifies: paging past the end is safe."""
        total = product_helper.list_products({"limit": 1}).json()["total"]
        body = product_helper.list_products({"skip": total + 100}).json()
        AssertHelper.assert_field_equals(body, "products", [])
        AssertHelper.assert_field_equals(body, "total", total)

    # case: TC-get-products-negative-invalid-limit
    @pytest.mark.parametrize("limit", ProductsTestData.INVALID_LIMITS)
    @allure.title("Invalid limit is rejected with 400")
    def test_invalid_limit_is_rejected_with_400(self, product_helper, limit):
        """RULE-products-invalid-paging-rejected. Verifies: bad paging input is rejected with a reason."""
        product_helper.list_products(
            {"limit": limit}, status_code=400, message="Invalid 'limit' - should be a positive number"
        )

    # case: TC-get-products-negative-negative-skip
    @allure.title("Negative skip is rejected with 400")
    def test_negative_skip_is_rejected_with_400(self, product_helper):
        """RULE-products-invalid-paging-rejected. Verifies: bad skip input is rejected with a reason."""
        product_helper.list_products(
            {"skip": -1}, status_code=400, message="Invalid 'skip' - should be a positive number"
        )

    # case: TC-get-products-happy-select-fields
    @pytest.mark.parametrize("select", ProductsTestData.SELECT_FORMS)
    @allure.title("select returns only the requested fields")
    def test_select_returns_only_requested_fields(self, product_helper, select):
        """RULE-products-select-fields: comma-separated or repeated select; id always included.
        Verifies: field selection trims the payload."""
        for product in product_helper.list_products({"limit": 5, **select}).json()["products"]:
            AssertHelper.assert_equals(set(product), {"id", "title", "price"}, f"fields of product {product['id']} ")

    # case: TC-get-products-happy-sort-by-price
    @pytest.mark.parametrize("order", ProductsTestData.SORT_ORDERS)
    @allure.title("Products sort by price")
    def test_sort_by_price(self, product_helper, order):
        """RULE-products-sort-by-order. Verifies: sorting covers the whole result."""
        body = product_helper.list_products({"sortBy": "price", "order": order, "limit": 0, "select": "price"}).json()
        prices = [product["price"] for product in body["products"]]
        AssertHelper.assert_equals(prices, sorted(prices, reverse=order == "desc"), f"prices sorted {order} ")

    # case: TC-get-products-negative-invalid-sort-order
    @allure.title("Invalid sort order is rejected with 400")
    def test_invalid_sort_order_is_rejected_with_400(self, product_helper):
        """RULE-products-sort-by-order. Verifies: bad sort input is rejected with a reason."""
        product_helper.list_products(
            {"sortBy": "price", "order": "sideways"},
            status_code=400,
            message="Invalid 'order' - should be either 'asc' or 'desc'",
        )

    # case: TC-get-products-boundary-unknown-sort-field-ignored
    @allure.title("Unknown sort field is ignored")
    def test_unknown_sort_field_is_ignored(self, product_helper):
        """RULE-products-sort-by-order (observed live: unknown sortBy ignored).
        Verifies: pins the observed fallback for an unknown field."""
        AssertHelper.assert_equals(
            product_helper.product_ids(product_helper.list_products({"sortBy": "nosuchfield", "limit": 5})),
            [1, 2, 3, 4, 5],
        )

    # case: TC-get-products-happy-modified-date-filter
    @pytest.mark.parametrize("use_after,use_before", ProductsTestData.DATE_FILTER_BOUNDS)
    @allure.title("modifiedAfter / modifiedBefore keep exactly the products in range")
    def test_modified_date_filter_matches_updated_at(self, product_helper, use_after, use_before):
        """RULE-products-modified-date-filter. Verifies: the date filter keeps exactly the products in range."""
        catalog = product_helper.list_products({"limit": 0, "select": "meta"}).json()["products"]
        stamps = [product["meta"]["updatedAt"] for product in catalog]
        after, before = pivot_between(stamps, 0.25), pivot_between(stamps, 0.75)
        params = {"limit": 0, "select": "meta"}
        if use_after:
            params["modifiedAfter"] = after
        if use_before:
            params["modifiedBefore"] = before

        expected = [
            product["id"]
            for product in catalog
            if (not use_after or parse_iso(product["meta"]["updatedAt"]) > parse_iso(after))
            and (not use_before or parse_iso(product["meta"]["updatedAt"]) < parse_iso(before))
        ]
        AssertHelper.assert_equals(
            sorted(product_helper.product_ids(product_helper.list_products(params))), sorted(expected), "filtered ids "
        )

    # case: TC-get-products-negative-invalid-modified-date
    @allure.title("Invalid modifiedAfter date is rejected with 400")
    def test_invalid_modified_date_is_rejected_with_400(self, product_helper):
        """RULE-products-modified-date-filter. Verifies: a bad date is rejected with a reason."""
        product_helper.list_products(
            {"modifiedAfter": "not-a-date"},
            status_code=400,
            message="Invalid 'modifiedAfter' - should be a valid ISO 8601 date, e.g. 2025-01-01T00:00:00Z",
        )

    # case: TC-get-products-boundary-delay-limit
    @pytest.mark.parametrize("delay,status_code", ProductsTestData.DELAYS)
    @allure.title("delay is limited to 5000 ms")
    def test_delay_is_limited_to_5000_ms(self, product_helper, delay, status_code):
        """RULE-products-delay-max-5000. Verifies: the documented delay range is enforced."""
        message = "Delay should be less than 5 seconds (5000 milliseconds)" if status_code == 400 else None
        product_helper.list_products({"limit": 1, "delay": delay}, status_code=status_code, message=message)

    # case: TC-get-products-error-shape-list-param-error-body
    @allure.title("List validation errors use the standard error body")
    def test_list_param_errors_use_standard_error_shape(self, product_helper):
        """Endpoint inventory: every error body is exactly {"message": <string>}.
        Verifies: validation errors use the standard body."""
        for params in ({"limit": "abc"}, {"sortBy": "price", "order": "sideways"}, {"modifiedAfter": "not-a-date"}):
            AssertHelper.assert_schema(product_helper.list_products(params, status_code=400).json(), ERROR_SCHEMA)
