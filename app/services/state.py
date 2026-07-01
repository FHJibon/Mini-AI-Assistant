import os
import json
import logging

logger = logging.getLogger(__name__)

CONVERSATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "conversations")

def get_history_file_path(user_id: str) -> str:
    os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
    safe_user_id = "".join([c for c in user_id if c.isalnum() or c in ("-", "_")]).strip()
    if not safe_user_id:
        safe_user_id = "default"
    return os.path.join(CONVERSATIONS_DIR, f"history_{safe_user_id}.json")

def load_session_history(user_id: str, session_id: str) -> list[dict]:
    file_path = get_history_file_path(user_id)
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(session_id, [])
    except Exception as e:
        logger.error(f"Error loading history for user {user_id}: {e}")
        return []

def save_session_history(user_id: str, session_id: str, history: list[dict]):
    file_path = get_history_file_path(user_id)
    data = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading history file for saving: {e}")
            
    data[session_id] = history
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error writing history file: {e}")
