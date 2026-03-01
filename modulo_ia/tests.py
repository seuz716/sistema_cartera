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
