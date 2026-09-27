# Resolved from the docs/products example output (inferred from example), with required-ness set by
# the live field census in context/api-context.md: 21 fields on all 194 products, `brand` on 102.
_PRODUCT_PROPERTIES = {
    "id": {"type": "integer"},
    "title": {"type": "string"},
    "description": {"type": "string"},
    "category": {"type": "string"},
    "price": {"type": "number", "minimum": 0},
    "discountPercentage": {"type": "number"},
    "rating": {"type": "number", "minimum": 0, "maximum": 5},
    "stock": {"type": "integer", "minimum": 0},
    "tags": {"type": "array", "items": {"type": "string"}},
    "brand": {"type": "string"},
    "sku": {"type": "string"},
    "weight": {"type": "number"},
    "dimensions": {
        "type": "object",
        "properties": {"width": {"type": "number"}, "height": {"type": "number"}, "depth": {"type": "number"}},
        "required": ["width", "height", "depth"],
        "additionalProperties": False,
    },
    "warrantyInformation": {"type": "string"},
    "shippingInformation": {"type": "string"},
    "availabilityStatus": {"type": "string"},
    "reviews": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "rating": {"type": "integer", "minimum": 1, "maximum": 5},
                "comment": {"type": "string"},
                "date": {"type": "string"},
                "reviewerName": {"type": "string"},
                "reviewerEmail": {"type": "string"},
            },
            "required": ["rating", "comment", "date", "reviewerName", "reviewerEmail"],
            "additionalProperties": False,
        },
    },
    "returnPolicy": {"type": "string"},
    "minimumOrderQuantity": {"type": "integer"},
    "meta": {
        "type": "object",
        "properties": {
            "createdAt": {"type": "string"},
            "updatedAt": {"type": "string"},
            "barcode": {"type": "string"},
            "qrCode": {"type": "string"},
        },
        "required": ["createdAt", "updatedAt", "barcode", "qrCode"],
        "additionalProperties": False,
    },
    "thumbnail": {"type": "string"},
    "images": {"type": "array", "items": {"type": "string"}},
}

PRODUCT_FIELDS = sorted(_PRODUCT_PROPERTIES)
_REQUIRED_PRODUCT_FIELDS = [field for field in PRODUCT_FIELDS if field != "brand"]

PRODUCT_SCHEMA = {
    "type": "object",
    "properties": _PRODUCT_PROPERTIES,
    "required": _REQUIRED_PRODUCT_FIELDS,
    "additionalProperties": False,
}

PRODUCT_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "products": {"type": "array", "items": PRODUCT_SCHEMA},
        "total": {"type": "integer", "minimum": 0},
        "skip": {"type": "integer", "minimum": 0},
        "limit": {"type": "integer", "minimum": 0},
    },
    "required": ["products", "total", "skip", "limit"],
    "additionalProperties": False,
}

# With `select`, each item holds only the chosen keys plus `id` (docs "Limit and skip products").
SELECTED_PRODUCT_LIST_SCHEMA = {
    **PRODUCT_LIST_SCHEMA,
    "properties": {
        **PRODUCT_LIST_SCHEMA["properties"],
        "products": {
            "type": "array",
            "items": {"type": "object", "properties": _PRODUCT_PROPERTIES, "required": ["id"]},
        },
    },
}

# Add/update docs examples: `{"id": ..., "title": ..., /* other product data */}` — the product's own
# fields with an id; which of the others come back isn't stated. (inferred from example)
WRITTEN_PRODUCT_SCHEMA = {
    "type": "object",
    "properties": _PRODUCT_PROPERTIES,
    "required": ["id"],
    "additionalProperties": False,
}

# docs/products "Delete a product": the deleted product plus `isDeleted` & `deletedOn`.
DELETED_PRODUCT_SCHEMA = {
    "type": "object",
    "properties": {
        **_PRODUCT_PROPERTIES,
        "isDeleted": {"const": True},
        "deletedOn": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$"},
    },
    "required": [*_REQUIRED_PRODUCT_FIELDS, "isDeleted", "deletedOn"],
    "additionalProperties": False,
}

# The docs' categories example isn't renderable as text; resolved from the live shape recorded in
# context/api-context.md's endpoint inventory. (inferred)
CATEGORY_LIST_SCHEMA = {
    "type": "array",
    "minItems": 1,
    "items": {
        "type": "object",
        "properties": {"slug": {"type": "string"}, "name": {"type": "string"}, "url": {"type": "string"}},
        "required": ["slug", "name", "url"],
        "additionalProperties": False,
    },
}

CATEGORY_SLUG_LIST_SCHEMA = {"type": "array", "minItems": 1, "items": {"type": "string"}}
