import allure
import pytest

from src.core.assert_helper import AssertHelper
from src.payload.product_payload import add_product_payload, update_product_payload
from tests.products.products_td import ProductsTestData

pytestmark = [pytest.mark.products, pytest.mark.regression]

TOKEN_REQUIRED = "Access Token is required"


@allure.feature("Products")
@allure.story("Bearer-protected product routes (/auth/products)")
class TestProtectedProductRoutes:
    # case: TC-get-auth-products-auth-authz-token-required
    @pytest.mark.smoke
    @allure.title("Protected product list requires a token")
    def test_protected_product_list_requires_token(self, product_helper, bearer_header):
        """RULE-auth-bearer-required-on-auth-routes. Verifies: the /auth/ mirror of a public route is locked."""
        product_helper.list_products_authenticated(None, status_code=401, message=TOKEN_REQUIRED)
        body = product_helper.list_products_authenticated(bearer_header, {"limit": 3}).json()
        AssertHelper.assert_equals(len(body["products"]), 3, "products returned ")

    # case: TC-post-auth-products-add-auth-authz-token-required
    @allure.title("Protected add requires a token")
    def test_protected_add_requires_token(self, product_helper, bearer_header):
        """RULE-auth-bearer-required-on-auth-routes. Verifies: the protected write route is locked."""
        product_helper.add_product_authenticated(add_product_payload(), None, status_code=401, message=TOKEN_REQUIRED)
        payload = add_product_payload()
        body = product_helper.add_product_authenticated(payload, bearer_header).json()
        AssertHelper.assert_field_equals(body, "title", payload["title"])
        product_helper.assert_product_not_persisted(body["id"])

    # case: TC-put-auth-products-id-auth-authz-token-required
    @pytest.mark.parametrize("method", ProductsTestData.PROTECTED_WRITE_METHODS)
    @allure.title("Protected update and delete require a token")
    def test_protected_update_and_delete_require_token(self, product_helper, bearer_header, method):
        """RULE-auth-bearer-required-on-auth-routes. Verifies: protected update/delete are locked."""
        original = product_helper.get_product(1).json()
        payload = update_product_payload(title="QA Protected")
        product_helper.write_product_authenticated(1, method, None, payload, status_code=401)
        product_helper.write_product_authenticated(1, method, bearer_header, payload)
        product_helper.assert_product_unchanged(1, original)
