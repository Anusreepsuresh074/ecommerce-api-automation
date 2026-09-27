from src.constants.endpoints.product_ep import (
    ADD_PRODUCT,
    AUTH_ADD_PRODUCT,
    AUTH_PRODUCT_BY_ID,
    AUTH_PRODUCTS,
    PRODUCT_BY_ID,
    PRODUCT_CATEGORIES,
    PRODUCT_CATEGORY_LIST,
    PRODUCT_SEARCH,
    PRODUCTS,
    PRODUCTS_BY_CATEGORY,
)
from src.core.assert_helper import AssertHelper
from src.schema.product_schema import (
    CATEGORY_LIST_SCHEMA,
    CATEGORY_SLUG_LIST_SCHEMA,
    DELETED_PRODUCT_SCHEMA,
    PRODUCT_LIST_SCHEMA,
    PRODUCT_SCHEMA,
    SELECTED_PRODUCT_LIST_SCHEMA,
    WRITTEN_PRODUCT_SCHEMA,
)
from src.utils.reporting import step


def _list_schema(params: dict | None) -> dict:
    return SELECTED_PRODUCT_LIST_SCHEMA if params and "select" in params else PRODUCT_LIST_SCHEMA


class ProductHelper:
    def __init__(self, api_base):
        self.api_base = api_base

    @staticmethod
    def product_ids(response) -> list[int]:
        """The ids on a product-list page, in response order."""
        return [product["id"] for product in response.json()["products"]]

    @step("List products")
    def list_products(self, params=None, status_code: int = 200, message=None):
        response = self.api_base.get(PRODUCTS, params=params)
        return AssertHelper.assert_response(response, status_code, _list_schema(params), message)

    @step("List products via the Bearer-protected route")
    def list_products_authenticated(self, headers, params=None, status_code: int = 200, message=None):
        response = self.api_base.get(AUTH_PRODUCTS, headers=headers, params=params)
        return AssertHelper.assert_response(response, status_code, _list_schema(params), message)

    @step("Search products for '{query}'")
    def search_products(self, query: str, params=None, status_code: int = 200):
        response = self.api_base.get(PRODUCT_SEARCH, params={"q": query, **(params or {})})
        return AssertHelper.assert_response(response, status_code, _list_schema(params), None)

    @step("Get product {product_id}")
    def get_product(self, product_id, status_code: int = 200, message=None):
        response = self.api_base.get(PRODUCT_BY_ID.format(product_id=product_id))
        return AssertHelper.assert_response(response, status_code, PRODUCT_SCHEMA, message)

    @step("List product categories")
    def list_categories(self):
        return AssertHelper.assert_response(self.api_base.get(PRODUCT_CATEGORIES), 200, CATEGORY_LIST_SCHEMA, None)

    @step("List category slugs")
    def list_category_slugs(self):
        return AssertHelper.assert_response(
            self.api_base.get(PRODUCT_CATEGORY_LIST), 200, CATEGORY_SLUG_LIST_SCHEMA, None
        )

    @step("List products in category '{slug}'")
    def list_by_category(self, slug: str, params=None, status_code: int = 200):
        response = self.api_base.get(PRODUCTS_BY_CATEGORY.format(slug=slug), params=params)
        return AssertHelper.assert_response(response, status_code, _list_schema(params), None)

    @step("Add a product")
    def add_product(self, payload: dict, status_code: int = 201):
        return AssertHelper.assert_response(
            self.api_base.post(ADD_PRODUCT, json=payload), status_code, WRITTEN_PRODUCT_SCHEMA, None
        )

    @step("Add a product via the Bearer-protected route")
    def add_product_authenticated(self, payload: dict, headers, status_code: int = 201, message=None):
        response = self.api_base.post(AUTH_ADD_PRODUCT, json=payload, headers=headers)
        return AssertHelper.assert_response(response, status_code, WRITTEN_PRODUCT_SCHEMA, message)

    @step("{method} product {product_id}")
    def update_product(self, product_id, payload: dict, method: str = "PUT", status_code: int = 200, message=None):
        if method not in ("PUT", "PATCH"):
            raise ValueError(f"update_product supports PUT or PATCH, got {method!r}")
        path = PRODUCT_BY_ID.format(product_id=product_id)
        response = self.api_base.put(path, json=payload) if method == "PUT" else self.api_base.patch(path, json=payload)
        return AssertHelper.assert_response(response, status_code, WRITTEN_PRODUCT_SCHEMA, message)

    @step("{method} product {product_id} via the Bearer-protected route")
    def write_product_authenticated(self, product_id, method: str, headers, payload=None, status_code: int = 200):
        if method not in ("PUT", "DELETE"):
            raise ValueError(f"write_product_authenticated supports PUT or DELETE, got {method!r}")
        path = AUTH_PRODUCT_BY_ID.format(product_id=product_id)
        if method == "DELETE":
            return AssertHelper.assert_response(
                self.api_base.delete(path, headers=headers), status_code, DELETED_PRODUCT_SCHEMA, None
            )
        return AssertHelper.assert_response(
            self.api_base.put(path, json=payload, headers=headers), status_code, WRITTEN_PRODUCT_SCHEMA, None
        )

    @step("Delete product {product_id}")
    def delete_product(self, product_id, status_code: int = 200, message=None):
        response = self.api_base.delete(PRODUCT_BY_ID.format(product_id=product_id))
        return AssertHelper.assert_response(response, status_code, DELETED_PRODUCT_SCHEMA, message)

    # Read-your-write. DummyJSON documents writes as simulated, so the verified state is non-persistence.

    @step("Read back: product {product_id} was not created")
    def assert_product_not_persisted(self, product_id):
        self.get_product(product_id, status_code=404)

    @step("Read back: product {product_id} is unchanged")
    def assert_product_unchanged(self, product_id, original: dict):
        AssertHelper.assert_equals(self.get_product(product_id).json(), original, f"product {product_id} on read-back ")
