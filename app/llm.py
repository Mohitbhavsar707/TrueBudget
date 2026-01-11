import json
from typing import Dict, Any, Optional
import requests


OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.1:8b"


def ollama_available() -> bool:
    try:
        r = requests.get("http://localhost:11434", timeout=1.5)
        return r.status_code in (200, 404)
    except Exception:
        return False


def generate_advice(payload: Dict[str, Any], model: str = DEFAULT_MODEL) -> str:
    """
    Generates plain-English advice. We keep math in code; the LLM explains and suggests.
    """
    system = (
        "You are a helpful budgeting coach. Use ONLY the numbers provided by the app. "
        "Do not invent income/expense values. "
        "Give short, actionable advice. If something is missing, ask a clarifying question."
    )

    user = (
        "Create a monthly budgeting explanation and tips using this JSON data.\n\n"
        f"{json.dumps(payload, indent=2)}\n\n"
        "Return:\n"
        "1) A short summary of the situation\n"
        "2) 3-6 bullet tips\n"
        "3) A simple next-steps checklist (3-5 items)\n"
        "Keep it friendly and not judgmental."
    )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }

    resp = requests.post(OLLAMA_URL, json=body, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]
