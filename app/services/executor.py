import logging
import json
from app.services.querying import get_order_status, search_product

logger = logging.getLogger(__name__)

def execute_tool_calls(tool_calls) -> list[dict]:
    tool_messages = []
    if not tool_calls:
        return tool_messages

    logger.info(f"Executing tool calls: {[tc.function.name for tc in tool_calls]}")
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        try:
            function_args = json.loads(tool_call.function.arguments)
        except Exception as e:
            logger.error(f"Error parsing arguments for tool {function_name}: {e}")
            function_args = {}

        if function_name == "get_order_status":
            tool_result = get_order_status(order_id=function_args.get("order_id"))
        elif function_name == "search_product":
            tool_result = search_product(name=function_args.get("name"))
        else:
            tool_result = {"error": f"Tool {function_name} not found."}

        tool_messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": function_name,
            "content": json.dumps(tool_result)
        })

    return tool_messages