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
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("ERROR: GEMINI_API_KEY no encontrada en las variables de entorno.")
            self.client = None
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            print(f"ERROR: No se pudo inicializar el cliente Gemini. Detalle: {e}")
            self.client = None

    def _get_model_name(self, complexity="standard"):
        """
        Retorna el modelo más económico disponible.
        """
        # gemini-2.0-flash-lite es el modelo de menor costo y alta eficiencia
        return "gemini-2.0-flash-lite"

    def analyze_data(self, data_context: str, complexity="standard") -> str:
        if not self.client:
            return "ERROR: Servicio de IA no disponible."

        model = self._get_model_name(complexity)

        system_prompt = "Analista de riesgos. Conciso. Español."

        prompt = f"{system_prompt}\n\nDATOS:\n{data_context}"

        try:
            print(f"Modelo: {model}")
            response = self.client.models.generate_content(
                model=model,
                contents=f"{system_prompt}\n\nDatos:\n{data_context}"
            )
            
            # Registrar uso real si es posible (enviando a un tracker si existiera aquí, 
            # pero el tracker está en views.py en este caso)
            return response.text
        except APIError as e:
            return f"Error de la API de Gemini: {e}"
        except Exception as e:
            return f"Error inesperado al generar contenido: {e}"
