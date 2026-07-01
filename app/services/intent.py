import logging
import json
from app.services.vector_store import openai
import app.config as config

logger = logging.getLogger(__name__)

async def classify_query_intent(query_text: str, history: list[dict]) -> str:
    """Classify the user's query intent into 'RETRIEVAL', 'TOOL_CALL', or 'DIRECT'."""
    try:
        # Format conversation history context for classification
        history_summary = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-3:]])
        
        system_content = (
            "You are an intent classifier for an AI Assistant. "
            "Your task is to classify the user's latest query into one of three categories:\n\n"
            "1. 'RETRIEVAL': The query requests specific information, guides, policies, or facts that would typically "
            "be found in uploaded documents (e.g., enterprise documentation, PDFs, text manuals).\n"
            "2. 'TOOL_CALL': The query requests checking order status (requires an Order ID like ORDXXX) "
            "or searching the product inventory for prices and stock availability.\n"
            "3. 'DIRECT': The query is a greeting, general chit-chat, a question about the conversation history "
            "itself (e.g., asking for their name, recalling previous topics), or general system prompts.\n\n"
            "Respond ONLY with a JSON object in this format: {\"intent\": \"RETRIEVAL\" | \"TOOL_CALL\" | \"DIRECT\"}. "
            "Do not include any explanation or extra characters."
        )

        response = await openai.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": f"History:\n{history_summary}\n\nLatest Query: {query_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_completion_tokens=50
        )
        
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        intent = data.get("intent", "DIRECT").upper()
        
        if intent not in ["RETRIEVAL", "TOOL_CALL", "DIRECT"]:
            intent = "DIRECT"
            
        logger.info(f"Classified intent for query '{query_text}': {intent}")
        return intent

    except Exception as e:
        logger.error(f"Error classifying query intent: {e}")
        # Fallback to RETRIEVAL to be safe if classification fails
        return "RETRIEVAL"
