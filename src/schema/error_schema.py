# No source documents DummyJSON's error body; every error observed while building context/api-context.md
# had exactly this shape. (inferred)
ERROR_SCHEMA = {
    "type": "object",
    "properties": {"message": {"type": "string", "minLength": 1}},
    "required": ["message"],
    "additionalProperties": False,
}
