from django.test import TestCase
from unittest.mock import patch, MagicMock
from .gemini_service import GeminiAIService


class GeminiServiceTests(TestCase):

    def test_analyze_data_no_client(self):
        """Sin cliente configurado, analyze_data debe retornar un mensaje de error."""
        with patch.dict("os.environ", {}, clear=True):
            # Forzar self.client = None
            service = GeminiAIService()
            service.client = None
            result = service.analyze_data("datos de prueba")
        self.assertIn("Error", result)

    def test_chat_response_no_client(self):
        """Sin cliente configurado, chat_response debe retornar un mensaje de error."""
        service = GeminiAIService.__new__(GeminiAIService)
        service.client = None
        result = service.chat_response("¿Cuántos clientes activos hay?")
        self.assertIn("Error", result)

    def test_model_is_flash(self):
        """El modelo debe ser gemini-2.5-flash-lite."""
        self.assertEqual(GeminiAIService.MODEL, "gemini-2.5-flash-lite")

    def test_analyze_data_calls_correct_model(self):
        """analyze_data debe llamar a la API con el modelo gemini-2.5-flash-lite."""
        service = GeminiAIService.__new__(GeminiAIService)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Análisis exitoso"
        mock_client.models.generate_content.return_value = mock_response
        service.client = mock_client

        result = service.analyze_data("clientes con deuda alta")

        # Verificar que se usó el modelo correcto
        call_kwargs = mock_client.models.generate_content.call_args
        self.assertEqual(call_kwargs.kwargs["model"], "gemini-2.5-flash-lite")
        self.assertEqual(result, "Análisis exitoso")

    def test_chat_response_calls_correct_model(self):
        """chat_response debe llamar a la API con el modelo gemini-2.5-flash-lite."""
        service = GeminiAIService.__new__(GeminiAIService)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Respuesta del chat"
        mock_client.models.generate_content.return_value = mock_response
        service.client = mock_client

        result = service.chat_response("¿Cómo registro un pago?")

        call_kwargs = mock_client.models.generate_content.call_args
        self.assertEqual(call_kwargs.kwargs["model"], "gemini-2.5-flash-lite")
        self.assertEqual(result, "Respuesta del chat")

    # --- NUEVAS PRUEBAS SENIOR ---
    
    def test_context_retriever_structure(self):
        """Verifica que el extractor de contexto devuelva las claves estratégicas esperadas."""
        from .context_retriever import build_context
        context = build_context()
        expected_keys = [
            "indicadores_30_dias", 
            "top_deudores", 
            "ventas_recientes", 
            "FECHA_ANALISIS"
        ]
        for key in expected_keys:
            self.assertIn(key, context, f"La clave {key} falta en el contexto.")

    @patch('modulo_ia.gemini_service.GeminiAIService.strategic_analysis')
    def test_strategic_analysis_returns_content(self, mock_analysis):
        """Simula un análisis estratégico y verifica que el servicio responda."""
        mock_analysis.return_value = "<html>Análisis estratégico de prueba</html>"
        service = GeminiAIService()
        result = service.strategic_analysis()
        self.assertEqual(result, "<html>Análisis estratégico de prueba</html>")


class ViewTests(TestCase):
    def setUp(self):
        from django.test import Client
        self.client = Client()

    def test_url_accessibility(self):
        """Verifica que las rutas del módulo existan (aunque fallen por login)."""
        from django.urls import reverse
        urls = ['ia_panel', 'ia_analisis']
        for url_name in urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302) # Redirect to login

