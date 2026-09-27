import uuid


def add_product_payload(**overrides) -> dict:
    """A complete new-product body with a unique title, so each test's data is its own."""
    payload = {
        "title": f"QA Test Product {uuid.uuid4().hex[:8]}",
        "description": "Created by an automated API test.",
        "price": 49.99,
        "category": "smartphones",
        "brand": "QA Brand",
        "stock": 10,
    }
    payload.update(overrides)
    return payload


def update_product_payload(**fields) -> dict:
    """Only the fields being changed — DummyJSON's PUT and PATCH both take a partial body (docs)."""
    return dict(fields)
