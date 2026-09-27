import allure
import pytest

from src.core.assert_helper import AssertHelper
from src.payload.product_payload import update_product_payload
from tests.products.products_td import ProductsTestData

pytestmark = [pytest.mark.products, pytest.mark.regression]


@allure.feature("Products")
@allure.story("Update and delete a product (simulated)")
class TestUpdateDeleteProduct:
    # case: TC-put-products-id-happy-applies-change-keeps-rest
    @allure.title("PUT applies the change and keeps other fields")
    def test_put_applies_the_change_and_keeps_other_fields(self, product_helper):
        """RULE-products-writes-simulated. Verifies: the change is applied, other fields kept."""
        original = product_helper.get_product(2).json()
        body = product_helper.update_product(2, update_product_payload(title="QA Renamed")).json()
        AssertHelper.assert_field_equals(body, "title", "QA Renamed")
        AssertHelper.assert_field_equals(body, "price", original["price"])
        product_helper.assert_product_unchanged(2, original)

    # case: TC-put-products-id-contract-schema-update-shape-same-as-get
    @pytest.mark.parametrize("method", ProductsTestData.UPDATE_METHODS)
    @pytest.mark.xfail(reason="Known API defect: PUT/PATCH return 11 of the product's 22 fields", strict=True)
    @allure.title("Update response has the same shape as GET")
    def test_update_response_has_same_shape_as_get(self, product_helper, method):
        """RULE-products-update-response-shape (inferred). Verifies: update and read return the same shape."""
        original = product_helper.get_product(5).json()
        updated = product_helper.update_product(5, update_product_payload(title="QA Shape"), method=method).json()
        product_helper.assert_product_unchanged(5, original)
        AssertHelper.assert_equals(set(updated), set(original), f"{method} response fields vs GET ")

    # case: TC-patch-products-id-happy-patch-not-persisted
    @allure.title("PATCH returns the change but does not persist it")
    def test_patch_changes_one_field_and_is_not_persisted(self, product_helper):
        """RULE-products-writes-simulated. Verifies: read-your-write: the change is returned but not saved."""
        original = product_helper.get_product(3).json()
        body = product_helper.update_product(3, update_product_payload(price=1.23), method="PATCH").json()
        AssertHelper.assert_field_equals(body, "price", 1.23)
        product_helper.assert_product_unchanged(3, original)

    # case: TC-delete-products-id-happy-delete-marker-not-persisted
    @allure.title("DELETE returns the deleted marker; the product still exists")
    def test_delete_returns_deleted_marker_and_is_not_persisted(self, product_helper):
        """RULE-products-writes-simulated (docs: returns isDeleted & deletedOn; "will not delete it").
        Verifies: delete returns the marker; the product still exists."""
        original = product_helper.get_product(4).json()
        body = product_helper.delete_product(4).json()  # DELETED_PRODUCT_SCHEMA in the helper
        AssertHelper.assert_field_equals(body, "id", 4)
        product_helper.assert_product_unchanged(4, original)

    # case: TC-put-products-id-negative-write-unknown-id
    @pytest.mark.parametrize("method", ProductsTestData.WRITE_METHODS)
    @allure.title("Writes to an unknown product return 404")
    def test_write_to_unknown_product_returns_404(self, product_helper, method):
        """RULE-products-unknown-id-not-found. Verifies: writes to missing products fail clearly."""
        message = "Product with id '99999' not found"
        if method == "DELETE":
            product_helper.delete_product(99999, status_code=404, message=message)
        else:
            product_helper.update_product(
                99999, update_product_payload(title="x"), method, status_code=404, message=message
            )
