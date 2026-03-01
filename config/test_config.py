import os
from django.test import TestCase
from django.conf import settings
from django.urls import reverse, resolve

class ConfigSecurityTest(TestCase):
    def test_secret_key_is_set(self):
        """Verifica que la SECRET_KEY no sea la por defecto en un entorno real."""
        self.assertNotEqual(settings.SECRET_KEY, 'default-key-if-not-found-change-me')

    def test_debug_mode_configured(self):
        """Verifica si DEBUG está configurado (importante para producción)."""
        # En el entorno de pruebas DEBUG es False por defecto, pero validamos la lógica del settings
        self.assertIsInstance(settings.DEBUG, bool)

    def test_gemini_api_key_loaded(self):
        """Asegura que la API Key de Gemini esté disponible para el modulo_ia."""
        self.assertTrue(hasattr(settings, 'GEMINI_API_KEY'))
        self.assertIsNotNone(settings.GEMINI_API_KEY)

class ConfigURLSTest(TestCase):
    def test_admin_url_works(self):
        """Verifica que la URL del admin sea accesible."""
        url = reverse('admin:index')
        self.assertEqual(resolve(url).func.__name__, 'index')
        response = self.client.get(url)
        # Redirige a login si no está autenticado, lo cual es correcto (302)
        self.assertIn(response.status_code, [200, 302])

    def test_static_and_media_configured(self):
        """Verifica configuración de carpetas de recursos."""
        self.assertTrue(settings.STATIC_URL)
        self.assertTrue(settings.MEDIA_URL)
        self.assertIsNotNone(settings.STATIC_ROOT)
        self.assertIsNotNone(settings.MEDIA_ROOT)
