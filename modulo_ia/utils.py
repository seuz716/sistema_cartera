import re

def count_tokens(text: str) -> int:
    """
    Cuenta tokens aproximados tipo Gemini/OpenAI.
    1 token ~ 4 caracteres.
    """
    text = text or ""
    return max(1, len(text) // 4)
