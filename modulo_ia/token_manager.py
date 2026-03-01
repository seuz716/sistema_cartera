import json
import os
import time
from google import genai

TOKEN_FILE = "token_usage.json"
DAILY_LIMIT = 200_000
DEFAULT_MODEL = "gemini-2.0-flash-lite"

def load_usage():
    if not os.path.exists(TOKEN_FILE):
        return {"date": time.strftime("%Y-%m-%d"), "used": 0, "method": "manual"}

    with open(TOKEN_FILE, "r") as file:
        data = json.load(file)
        if "method" not in data:
            data["method"] = "manual"
        return data

def save_usage(data):
    with open(TOKEN_FILE, "w") as file:
        json.dump(data, file)

def count_tokens(text, model=DEFAULT_MODEL, client=None):
    """
    Cuenta tokens reales usando la API si hay cliente disponible,
    de lo contrario usa estimación manual.
    """
    if not text:
        return 0

    if client:
        try:
            response = client.models.count_tokens(model=model, contents=text)
            return response.total_tokens
        except Exception:
            pass

    # Estimación si falla la API o no hay cliente
    return max(1, len(text) // 4)

def smart_truncate(text, max_tokens=1000, model=DEFAULT_MODEL, client=None):
    """
    Trunca el texto inteligentemente si excede los tokens.
    Mantiene el final (que suele ser la instrucción más reciente).
    """
    current_tokens = count_tokens(text, model, client)
    if current_tokens <= max_tokens:
        return text

    # Si excede, cortamos proporcionalmente y añadimos una nota
    # Un enfoque simple: quedarnos con los últimos MAX_TOKENS * 4 caracteres
    cutoff = max_tokens * 4
    truncated_text = "... [Contexto truncado por límite de tokens] ...\n" + text[-cutoff:]
    return truncated_text

def register_tokens(n, method="real"):
    data = load_usage()
    today = time.strftime("%Y-%m-%d")

    if data["date"] != today:
        data = {"date": today, "used": 0, "method": method}

    data["used"] += n
    data["method"] = method
    save_usage(data)

def remaining_tokens():
    data = load_usage()
    try:
        used = int(data.get("used", 0))
    except (ValueError, TypeError):
        used = 0
    return DAILY_LIMIT - used

def can_use(n):
    return remaining_tokens() >= n
