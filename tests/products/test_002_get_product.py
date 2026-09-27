import allure
import pytest

from src.core.assert_helper import AssertHelper
from src.schema.error_schema import ERROR_SCHEMA
from src.schema.product_schema import PRODUCT_SCHEMA
from tests.products.products_td import ProductsTestData

pytestmark = [pytest.mark.products, pytest.mark.regression]


@allure.feature("Products")
@allure.story("Get one product")
class TestGetProduct:
    # case: TC-get-products-id-happy-existing-id
    @pytest.mark.smoke
    @allure.title("Get a product by id")
    def test_get_product_by_id(self, product_helper):
        """Endpoint inventory: GET /products/{id}. Verifies: a product can be fetched by id."""
        AssertHelper.assert_field_equals(product_helper.get_product(1).json(), "id", 1)

    # case: TC-get-products-id-contract-schema-product-shape
    @allure.title("A product matches Product")
    def test_product_matches_schema(self, product_helper):
        """Endpoint inventory: Product. Verifies: a single product has exactly the Product shape."""
        AssertHelper.assert_schema(product_helper.get_product(1).json(), PRODUCT_SCHEMA)

    # case: TC-get-products-id-contract-schema-list-detail-agree
    @allure.title("List and detail return the same record")
    def test_list_and_detail_return_the_same_record(self, product_helper):
        """Endpoint inventory: list item and detail record are identical (observed live).
        Verifies: both routes return the same record."""
        from_list = product_helper.list_products({"limit": 1, "skip": 4}).json()["products"][0]
        AssertHelper.assert_equals(product_helper.get_product(from_list["id"]).json(), from_list, "detail vs list ")

    # case: TC-get-products-id-negative-unknown-id
    @pytest.mark.parametrize("product_id", ProductsTestData.UNKNOWN_IDS)
    @allure.title("Unknown product id returns 404 with a reason")
    def test_unknown_product_returns_404_with_reason(self, product_helper, product_id):
        """RULE-products-unknown-id-not-found. Verifies: unknown ids fail with a useful message."""
        product_helper.get_product(product_id, status_code=404, message=f"Product with id '{product_id}' not found")

    # case: TC-get-products-id-error-shape-not-found-body
    @allure.title("404 uses the standard error body")
    def test_not_found_uses_standard_error_shape(self, product_helper):
        """Endpoint inventory: every error body is exactly {"message": <string>}.
        Verifies: 404 uses the standard body."""
        AssertHelper.assert_schema(product_helper.get_product(99999, status_code=404).json(), ERROR_SCHEMA)
