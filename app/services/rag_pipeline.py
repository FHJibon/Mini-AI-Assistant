import logging
import app.config as config
from app.services.vector_store import query_vector_store, openai

logger = logging.getLogger(__name__)

async def get_rag_response(query_text: str, top_k: int = 4) -> str:
    if query_text.lower().strip().rstrip("?.!") in {
        "hi", "hello", "hey", "greetings", "hi there", "hello there", 
        "good morning", "good afternoon", "good evening"
    }:
        return "Hi there! How can I help you with ERP today?"

    try:
        logger.info(f"Retrieving context for query: {query_text}")
        matching_chunks = await query_vector_store(query_text, top_k=top_k)
        if not matching_chunks:
            return "I couldn't find that information in the uploaded documents."

        response = await openai.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Answer the user's question using ONLY the provided document context.\n"
                        "Rules:\n"
                        "1. Rely ONLY on the provided context. Do not use external knowledge.\n"
                        "2. If the answer cannot be found in the context, reply 'I couldn't find that information in the uploaded documents.'\n"
                        "3. Keep the answer direct, friendly, and concise (max 2 sentences, humanized style).\n\n"
                        f"Context:\n{'\n\n'.join(matching_chunks)}"
                    )
                },
                {"role": "user", "content": query_text}
            ],
            temperature=0.3,
            max_completion_tokens=800
        )
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error in RAG pipeline: {e}")
        return f"Error: {e}"
