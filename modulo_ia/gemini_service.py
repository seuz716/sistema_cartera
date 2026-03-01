from google import genai
from google.genai.errors import APIError
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class GeminiAIService:
    """
    Servicio para interactuar con los modelos Gemini de Google.
    Usa el modelo estándar gemini-2.0-flash para evitar límites de cuota reducidos.
    """

    MODEL = "gemini-2.5-flash-lite" 

    # ------------------------------------------------------------------
    # Prompt de sistema para el analisis de datos de cartera de credito.
    # Instruye al modelo a ser conciso, estructurado y enfocado al negocio.
    # ------------------------------------------------------------------
    SYSTEM_PROMPT_ANALISIS = (
        "Eres un analista experto en carteras de credito y riesgo financiero. "
        "Responde SIEMPRE en espanol siempre justificado el texto de respuesta. "
        "Cuando recibas datos de clientes, productos o cartera, genera un analisis breve con estas secciones:\n"
        "1. Resumen ejecutivo (2-3 oraciones).\n"
        "2. Hallazgos clave (lista de maximo 5 puntos).\n"
        "3. Recomendaciones accionables (lista de maximo 3 puntos).\n"
        "Se directo. Usa cifras cuando esten disponibles. No repitas los datos de entrada."
    )

    # ------------------------------------------------------------------
    # Prompt de sistema para el chat de asistencia al usuario del sistema.
    # ------------------------------------------------------------------
    SYSTEM_PROMPT_CHAT = (
        "Eres un analista financiero experto de CarteraPro. "
        "Responde siempre en español con el texto JUSTIFICADO (usando etiquetas <p style='text-align: justify;'> si es necesario). "
        "USAR SIEMPRE HTML como formato final. Nunca Markdown. "
        "REGLAS DE FORMATO Y LÓGICA DE AUDITORÍA:\n"
        "1. TABLAS: Usa <table class='table table-striped table-bordered table-sm'>.\n"
        "2. ESTILOS: Solo clases de Bootstrap. Sin estilos inline excepto el 'text-align: justify' solicitado.\n"
        "3. DASHBOARDS: Encuadra en <div class='dashboard-block'>.\n"
        "4. GRÁFICOS: Genera contenedores <div class='chart-data' data-chart-type='...' data-values='...' data-labels='...'> cuando detectes métricas comparativas.\n"
        "5. CÁLCULOS DETERMINÍSTICOS (OBLIGATORIO): Si el contexto tiene la 'FECHA_ACTUAL' y ves registros de fechas de 'pagos' o 'ventas' del cliente consultado, DEBES calcular la antigüedad o días transcurridos. No digas 'no se puede' si tienes la fecha ahí. Si hoy es 2026-03-01 y el pago fue 2026-03-01, responde: 'El último pago fue hoy mismo (hace 0 días)'.\n"
        "6. HONESTIDAD DE DATOS: Solo si el cliente NO aparece en absoluto en el contexto (ventas, pagos o clientes), explica que no lo visualizas en los últimos 50 registros y pide el ID o Nombre exacto para buscarlo.\n"
        "7. Sé conciso, analítico y profesional.\n"
    )

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
        reraise=True
    )
    def _call_gemini_api(self, prompt: str) -> str:
        """Llamada interna con reintentos para manejar límites de cuota (429)."""
        if not self.client:
            raise Exception("Servicio de IA no disponible.")
        
        response = self.client.models.generate_content(
            model=self.MODEL,
            contents=prompt,
        )
        return response.text

    def analyze_data(self, data_context: str) -> str:
        """Analiza datos de cartera usando el prompt especializado de analisis."""
        prompt = f"{self.SYSTEM_PROMPT_ANALISIS}\n\nDATOS A ANALIZAR:\n{data_context}"
        return self._safe_execute(prompt, "analyze_data")

    def chat_response(self, message: str) -> str:
        """Responde a un mensaje de chat con contexto del sistema de cartera."""
        from .context_retriever import build_context
        from django.utils import timezone
        import json

        context = build_context()
        context['FECHA_ACTUAL'] = str(timezone.now().date())

        prompt = (
            f"{self.SYSTEM_PROMPT_CHAT}\n\n"
            f"=== CONTEXTO DEL SISTEMA ===\n"
            f"{json.dumps(context, ensure_ascii=False, indent=2, default=str)}\n\n"
            f"=== PREGUNTA DEL USUARIO ===\n"
            f"{message}"
        )

        return self._safe_execute(prompt, "chat_response")

    def _safe_execute(self, prompt: str, action: str) -> str:
        """Envuelve la llamada a la API con manejo de errores global."""
        try:
            print(f"Modelo: {self.MODEL} | Accion: {action}")
            return self._call_gemini_api(prompt)
        except APIError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                return "Error: Se ha agotado la cuota de la IA (Límite 429). Por favor, intenta de nuevo en un momento."
            return f"Error de la API de Gemini: {e}"
        except Exception as e:
            return f"Error inesperado de IA: {e}"
