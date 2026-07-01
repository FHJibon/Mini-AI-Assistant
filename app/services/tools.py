import json
import os
import logging

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def get_order_status(order_id: str) -> dict:
    """Get the status and estimated delivery date of an order using its order ID."""
    try:
        file_path = os.path.join(DATA_DIR, "orders.json")
        if not os.path.exists(file_path):
            logger.error(f"Orders file not found at {file_path}")
            return {"error": "Orders database not found."}
        with open(file_path, "r", encoding="utf-8") as f:
            orders = json.load(f)
        for order in orders:
            if order.get("order_id") == order_id:
                return {
                    "order_id": order.get("order_id"),
                    "status": order.get("status"),
                    "estimated_delivery": order.get("estimated_delivery")
                }
        return {"error": f"Order {order_id} not found."}
    except Exception as e:
        logger.error(f"Error reading orders database: {e}")
        return {"error": f"Error retrieving order status: {str(e)}"}

def search_product(name: str) -> dict:
    """Search for a product by its name to get its price and stock availability."""
    try:
        file_path = os.path.join(DATA_DIR, "products.json")
        if not os.path.exists(file_path):
            logger.error(f"Products file not found at {file_path}")
            return {"error": "Products database not found."}
        with open(file_path, "r", encoding="utf-8") as f:
            products = json.load(f)
        
        query = name.lower().strip()
        results = []
        for product in products:
            p_name = product.get("name", "")
            if query in p_name.lower():
                results.append({
                    "name": p_name,
                    "price": product.get("price"),
                    "stock": product.get("stock")
                })
        if results:
            return {"products": results}
        return {"error": f"No products matching '{name}' found."}
    except Exception as e:
        logger.error(f"Error reading products database: {e}")
        return {"error": f"Error searching products: {str(e)}"}

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
                        "description": "The unique identifier of the order, e.g., 'ORD001'.",
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
                        "description": "The name of the product or keywords to search for, e.g., 'Wireless Mouse'.",
                    }
                },
                "required": ["name"],
            },
        }
    }
]
