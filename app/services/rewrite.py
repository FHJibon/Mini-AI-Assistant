import logging
from app.services.embed import openai
import app.config as config

logger = logging.getLogger(__name__)

async def condense_query(query_text: str, history: list[dict]) -> str:
    if not history:
        return query_text
    try:
        history_summary = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-5:]])
        response = await openai.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Given the following conversation history and the latest user question, "
                        "reformulate the question to be a standalone query that captures all necessary context. "
                        "Do not answer the question, just return the reformulated standalone query."
                    )
                },
                {"role": "user", "content": f"History:\n{history_summary}\n\nLatest Question: {query_text}"}
            ],
            temperature=0.0,
            max_completion_tokens=200
        )
        condensed = response.choices[0].message.content.strip()
        logger.info(f"Condensed query: '{query_text}' -> '{condensed}'")
        return condensed
    except Exception as e:
        logger.error(f"Error condensing query: {e}")
        return query_text
