import logging
import json
import app.config as config
from app.services.embed import openai
from app.utils.state import load_session_history, save_session_history
from app.services.intent import classify_query_intent
from app.services.rewrite import condense_query
from app.utils.executor import execute_tool_calls
from app.services.vector import query_vector_store
from app.utils.specify import OPENAI_TOOLS

logger = logging.getLogger(__name__)

async def get_rag_response(query_text: str, user_id: str = "default", session_id: str = "default", top_k: int = 4) -> str:
    try:

        history = load_session_history(user_id, session_id)

        condensed_query = await condense_query(query_text, history)

        intent = await classify_query_intent(condensed_query, history)

        matching_chunks = []
        use_tools = None
        if intent == "RETRIEVAL":
            logger.info("Routing query to RETRIEVAL pipeline.")
            matching_chunks = await query_vector_store(condensed_query, top_k=top_k)
            system_content = (
                "Answer the user's question using ONLY the provided document context.\n"
                "Rules:\n"
                "1. If the answer cannot be found in the document context, you MUST reply exactly: "
                "'I couldn't find that information in the uploaded documents.'\n"
                "2. Keep the answer direct, friendly, and concise (max 2 sentences, humanized style).\n\n"
                f"Document Context:\n{'\n\n'.join(matching_chunks)}"
            )
        elif intent == "TOOL_CALL":
            logger.info("Routing query to TOOL_CALL pipeline.")
            use_tools = OPENAI_TOOLS
            system_content = (
                "You are a helpful assistant with access to order status inquiries and product searches.\n"
                "Rules:\n"
                "1. Use the tools to retrive information when asked about orders or products.\n"
                "2. Reply simply about the product satutes and nothing else or asking about anything\n"
                "3. Keep the answer direct, friendly, and concise (max 2 sentences, humanized style)."
            )
        else: 
            logger.info("Routing query to DIRECT chat pipeline.")
            system_content = (
                "You are a helpful and friendly AI assistant.\n"
                "Rules:\n"
                "1. Answer the user directly, leveraging conversation history, if present.\n"
                "2. Keep the answer direct, friendly, and concise (max 2 sentences, humanized style)."
            )

        messages = [{"role": "system", "content": system_content}]

        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
 
        messages.append({"role": "user", "content": query_text})

        response = await openai.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            tools=use_tools,
            tool_choice="auto" if use_tools else None,
            temperature=0.3,
            max_completion_tokens=800
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if intent == "TOOL_CALL" and tool_calls:
            messages.append(response_message)
            tool_messages = execute_tool_calls(tool_calls)
            messages.extend(tool_messages)
            response2 = await openai.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
                temperature=0.3,
                max_completion_tokens=800
            )
            answer = response2.choices[0].message.content.strip()
        else:
            answer = response_message.content.strip()

        history.append({"role": "user", "content": query_text})
        history.append({"role": "assistant", "content": answer})
        save_session_history(user_id, session_id, history)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error in AI pipeline: {e}")
        return f"Error: {e}"
