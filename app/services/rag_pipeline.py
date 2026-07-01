import logging
import app.config as config
from app.services.vector_store import query_vector_store, openai
from app.services.context import load_session_history, save_session_history, condense_query

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
                    "Answer the user's question using ONLY the provided document context or conversation history.\n"
                    "Rules:\n"
                    "1. Rely ONLY on the provided context. Do not use external knowledge.\n"
                    "2. If the answer cannot be found in the context or conversation history, reply 'I couldn't find that information in the uploaded documents.'\n"
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

        # Call OpenAI Chat Completion API
        response = await openai.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            temperature=0.3,
            max_completion_tokens=800
        )
        answer = response.choices[0].message.content.strip()
        
        # Update and save session history
        history.append({"role": "user", "content": query_text})
        history.append({"role": "assistant", "content": answer})
        save_session_history(user_id, session_id, history)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error in RAG pipeline: {e}")
        return f"Error: {e}"
