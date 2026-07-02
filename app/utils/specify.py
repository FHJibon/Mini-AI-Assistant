OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Retrieve the status and estimated delivery date for a specific order by its order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The unique identifier of the order.",
                    }
                },
                "required": ["order_id"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_product",
            "description": "Search the product database by product name to get price and stock availability details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the product or keywords to search for.",
                    }
                },
                "required": ["name"],
            },
        }
    }
]
