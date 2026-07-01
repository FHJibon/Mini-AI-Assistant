import logging
import json
import app.config as config
from app.services.vector_store import query_vector_store, openai
from app.services.context import load_session_history, save_session_history, condense_query
from app.services.tools import OPENAI_TOOLS, get_order_status, search_product

logger = logging.getLogger(__name__)

async def get_rag_response(query_text: str, user_id: str = "default", session_id: str = "default", top_k: int = 4) -> str:
    if query_text.lower().strip().rstrip("?.!") in {
        "hi", "hello", "hey", "greetings", "hi there", "hello there", 
        "good morning", "good afternoon", "good evening"
    }:
        return "Hi there! How can I help you with ERP today?"

    try:
        # Load conversation history from disk
        history = load_session_history(user_id, session_id)
        
        # Condense the query based on conversation history
        condensed_query = await condense_query(query_text, history)
        
        # Retrieve context from Pinecone using condensed query
        logger.info(f"Retrieving context for query: {condensed_query}")
        matching_chunks = await query_vector_store(condensed_query, top_k=top_k)

        # Build prompt message list
        messages = [
            {
                "role": "system",
                "content": (
                    "Answer the user's question using the provided document context, conversation history, or results from tools.\n"
                    "Rules:\n"
                    "1. Rely ONLY on the provided context, conversation history, or results from tools. Do not use external knowledge.\n"
                    "2. If the answer cannot be found in the context, conversation history, or tool results, reply 'I couldn't find that information in the uploaded documents.'\n"
                    "3. Keep the answer direct, friendly, and concise (max 2 sentences, humanized style).\n\n"
                    f"Context:\n{'\n\n'.join(matching_chunks)}"
                )
            }
        ]
        
        # Append message history (excluding system messages)
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        # Append the new user question
        messages.append({"role": "user", "content": query_text})

        # Call OpenAI Chat Completion API with tool definitions
        response = await openai.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            tools=OPENAI_TOOLS,
            tool_choice="auto",
            temperature=0.3,
            max_completion_tokens=800
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        if tool_calls:
            logger.info(f"Tool calls requested: {[tc.function.name for tc in tool_calls]}")
            # Append assistant message with tool calls to messages
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except Exception as e:
                    logger.error(f"Error parsing tool arguments: {e}")
                    function_args = {}
                
                if function_name == "get_order_status":
                    tool_result = get_order_status(order_id=function_args.get("order_id"))
                elif function_name == "search_product":
                    tool_result = search_product(name=function_args.get("name"))
                else:
                    tool_result = {"error": f"Tool {function_name} not found."}
                
                # Append tool message with result
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_result)
                })
            
            # Request second response from OpenAI
            response2 = await openai.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
                temperature=0.3,
                max_completion_tokens=800
            )
            answer = response2.choices[0].message.content.strip()
        else:
            answer = response_message.content.strip()
        
        # Update and save session history
        history.append({"role": "user", "content": query_text})
        history.append({"role": "assistant", "content": answer})
        save_session_history(user_id, session_id, history)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error in RAG pipeline: {e}")
        return f"Error: {e}"
