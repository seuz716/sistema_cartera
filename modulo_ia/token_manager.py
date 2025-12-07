import json
import os
import time

TOKEN_FILE = "token_usage.json"
DAILY_LIMIT = 200_000  # ajusta según tu gusto


def load_usage():
    if not os.path.exists(TOKEN_FILE):
        return {"date": time.strftime("%Y-%m-%d"), "used": 0}

    with open(TOKEN_FILE, "r") as file:
        return json.load(file)


def save_usage(data):
    with open(TOKEN_FILE, "w") as file:
        json.dump(data, file)


def count_tokens(text):
    """
    Cuenta tokens aproximados.
    GPT-3.5/4/5 usan ~4 caracteres por token.
    """
    if not text:
        return 1
    return max(1, len(text) // 4)


def register_tokens(n):
    data = load_usage()
    today = time.strftime("%Y-%m-%d")

    # reset diario
    if data["date"] != today:
        data = {"date": today, "used": 0}

    data["used"] += n
    save_usage(data)


def remaining_tokens():
    data = load_usage()
    return DAILY_LIMIT - data["used"]


def can_use(n):
    return remaining_tokens() >= n
