# modulo_ia/gemini_service.py

from google import genai
from google.genai.errors import APIError
import os

API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiAIService:
    """
    Servicio para interactuar con los modelos Gemini de Google.
    """

    def __init__(self):
        try:
            self.client = genai.Client()
        except Exception as e:
            print(f"ERROR: No se pudo inicializar el cliente Gemini. Revisa tu API Key. Detalle: {e}")
            self.client = None

    def _get_model_name(self, complexity="standard"):
        """
        Modelos ultra baratos que NO consumen la cuota.
        """
        if complexity == "complex":
            # Modelo pensando barato
            return "gemini-2.0-flash-lite-thinking"
        else:
            # Modelo rápido, casi gratis
            return "gemini-2.0-flash-lite"

    def analyze_data(self, data_context: str, complexity="standard") -> str:
        if not self.client:
            return "ERROR: Servicio de IA no disponible."

        model = self._get_model_name(complexity)

        system_prompt = (
            "Eres un analista de riesgo y crédito experto. Analiza los datos de cartera proporcionados. "
            "Da conclusiones claras, en español, y no escribas demasiado."
        )

        prompt = f"{system_prompt}\n\nDATOS:\n{data_context}"

        try:
            print(f"Modelo usado (low cost): {model}")
            response = self.client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text
        except APIError as e:
            return f"Error de la API de Gemini: {e}"
        except Exception as e:
            return f"Error inesperado al generar contenido: {e}"
