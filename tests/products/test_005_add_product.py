import allure
import pytest

from src.core.assert_helper import AssertHelper
from src.payload.product_payload import add_product_payload

pytestmark = [pytest.mark.products, pytest.mark.regression]


@allure.feature("Products")
@allure.story("Add a product (simulated)")
class TestAddProduct:
    """DummyJSON simulates writes (RULE-products-writes-simulated), so read-your-write asserts the
    documented non-persistence through GET /products/{id}."""

    # case: TC-post-products-add-happy-echoes-with-new-id
    @pytest.mark.smoke
    @allure.title("Add echoes the product with a new id")
    def test_add_product_echoes_it_with_a_new_id(self, product_helper):
        """RULE-products-writes-simulated. Verifies: add returns the product with a new id."""
        payload = add_product_payload()
        body = product_helper.add_product(payload).json()
        AssertHelper.assert_is_instance(body.get("id"), int, "new product id ")
        for field, value in payload.items():
            AssertHelper.assert_field_equals(body, field, value)
        product_helper.assert_product_not_persisted(body["id"])

    # case: TC-post-products-add-happy-added-not-persisted
    @allure.title("An added product is not persisted")
    def test_added_product_is_not_persisted(self, product_helper):
        """RULE-products-writes-simulated. Verifies: read-your-write: the documented simulation."""
        new_id = product_helper.add_product(add_product_payload()).json()["id"]
        product_helper.assert_product_not_persisted(new_id)

    # case: TC-post-products-add-negative-empty-body
    @pytest.mark.xfail(reason="Known API defect: an empty body is accepted (201)", strict=True)
    @allure.title("Empty body is rejected")
    def test_add_product_with_empty_body_is_rejected(self, product_helper):
        """RULE-products-add-validates-body (inferred). Verifies: a product needs content."""
        product_helper.add_product({}, status_code=400)

    # case: TC-post-products-add-negative-wrong-field-type
    @pytest.mark.xfail(reason="Known API defect: a string price is accepted and echoed (201)", strict=True)
    @allure.title("Wrong price type is rejected")
    def test_add_product_with_wrong_price_type_is_rejected(self, product_helper):
        """RULE-products-add-validates-body (inferred). Verifies: field types are validated."""
        product_helper.add_product(add_product_payload(price="free"), status_code=400)
