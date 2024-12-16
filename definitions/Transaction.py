import jsonschema

schema = {
    "type": "object",
    "properties": {
        "sum": {
            "type": "float",
            "minLength": 1
        },
        "user_id": {
            "type": "integer",
            "minimum": 1
        },
        "transaction_id": {
            "type": "integer",
            "minimum": 1
        }
    },
    "required": ["sum", "user_id"]
}

