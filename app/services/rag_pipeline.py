import logging
import json
import app.config as config
from app.services.vector_store import query_vector_store, openai
from app.services.context import load_session_history, save_session_history
from app.services.intent import classify_query_intent
from app.services.query_rewriter import condense_query
from app.services.tool_executor import execute_tool_calls
from app.services.tools import OPENAI_TOOLS

logger = logging.getLogger(__name__)

async def get_rag_response(query_text: str, user_id: str = "default", session_id: str = "default", top_k: int = 4) -> str:
    try:
        # 1. Load conversation history
        history = load_session_history(user_id, session_id)
        
        # 2. Condense the query based on conversation history (resolves pronouns / context)
        condensed_query = await condense_query(query_text, history)
        
        # 3. Decide query intent (RETRIEVAL, TOOL_CALL, or DIRECT)
        intent = await classify_query_intent(condensed_query, history)
        
        # Initialize context and tools variables
        matching_chunks = []
        use_tools = None
        
        # 4. Route execution depending on the classified intent
        if intent == "RETRIEVAL":
            logger.info("Routing query to RETRIEVAL pipeline.")
            # Execute retrieval only when needed
            matching_chunks = await query_vector_store(condensed_query, top_k=top_k)
            system_content = (
                "Answer the user's question using ONLY the provided document context and conversation history.\n"
                "Rules:\n"
                "1. Rely ONLY on the provided document context and conversation history. Do not use external knowledge.\n"
                "2. If the answer cannot be found in the context or conversation history, you MUST reply exactly: "
                "'I couldn't find that information in the uploaded documents.'\n"
                "3. Keep the answer direct, friendly, and concise (max 2 sentences, humanized style).\n\n"
                f"Document Context:\n{'\n\n'.join(matching_chunks)}"
            )
        elif intent == "TOOL_CALL":
            logger.info("Routing query to TOOL_CALL pipeline.")
            use_tools = OPENAI_TOOLS
            system_content = (
                "You are an assistant with access to mock tools for order status inquiries and product searches.\n"
                "Rules:\n"
                "1. If the user is asking about a product or order, invoke the appropriate tool.\n"
                "2. If a tool returns an error or no results, explain that clearly to the user.\n"
                "3. Keep the answer direct, friendly, and concise (max 2 sentences, humanized style)."
            )
        else: # DIRECT
            logger.info("Routing query to DIRECT chat pipeline.")
            system_content = (
                "You are a helpful and friendly AI assistant.\n"
                "Rules:\n"
                "1. Answer the user directly, leveraging conversation history (such as names or preferences) if present.\n"
                "2. Do not attempt to search files or invoke mock tools.\n"
                "3. Keep the answer direct, friendly, and concise (max 2 sentences, humanized style)."
            )

        # 5. Build system prompt message list
        messages = [{"role": "system", "content": system_content}]
        
        # Append message history (excluding system messages)
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        # Append the new user question
        messages.append({"role": "user", "content": query_text})

        # 6. Call OpenAI Chat Completion
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
        
        # 7. Execute tool call if needed
        if intent == "TOOL_CALL" and tool_calls:
            messages.append(response_message)
            tool_messages = execute_tool_calls(tool_calls)
            messages.extend(tool_messages)
            
            # Request second response from OpenAI with tool results
            response2 = await openai.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
                temperature=0.3,
                max_completion_tokens=800
            )
            answer = response2.choices[0].message.content.strip()
        else:
            answer = response_message.content.strip()
            
        # 8. Save updated session history
        history.append({"role": "user", "content": query_text})
        history.append({"role": "assistant", "content": answer})
        save_session_history(user_id, session_id, history)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error in RAG pipeline: {e}")
        return f"Error: {e}"
