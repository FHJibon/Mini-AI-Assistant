import logging
import json
from app.services.embed import openai
import app.config as config

logger = logging.getLogger(__name__)

async def classify_query_intent(query_text: str, history: list[dict]) -> str:
    try:
        history_summary = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-3:]])
        
        system_content = (
            "You are a high-precision intent classifier for an AI Assistant. "
            "Your task is to classify the user's latest query into one of three categories:\n\n"
            "1. 'RETRIEVAL': Select this when the query asks a factual question, requests an explanation of a concept, "
            "asks for definitions of terms, seeks general knowledge, or inquires about policies. "
            "All factual lookups and logical definition queries must be classified here to prevent the assistant "
            "from answering directly using its own pre-trained knowledge.\n"
            "2. 'TOOL_CALL': Select this when the query requests order status using an Order ID, "
            "or searches product catalog details including prices and stock availability."
            "And also Highest or Lowest price item or product queries must be classified here too.\n"
            "3. 'DIRECT': Select this strictly for simple greetings, expressions of thanks, closing salutations, "
            "or queries requesting details from the active conversation history itself "
            "Factual or informational queries must never be classified as DIRECT.\n\n"
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
        return "RETRIEVAL"