import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from clientes.models import Cliente
from ventas.models import Venta, DetalleVenta
from cartera.models import Pago
from unittest.mock import patch

@pytest.mark.django_db
class TestIntegracionCartera:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="testuser", password="password123")

    @pytest.fixture
    def client_auth(self, client, user):
        client.login(username="testuser", password="password123")
        return client

    def test_flujo_completo_cartera(self, client_auth):
        # 1. Crear Cliente
        cliente = Cliente.objects.create(
            numero_identificacion="12345",
            nombre="Cesar",
            apellido="Prueba",
            tipo_persona="natural",
            email="cesar@test.com",
            forma_pago="contado"
        )
        assert Cliente.objects.count() == 1

        # 2. Crear Venta
        venta = Venta.objects.create(
            cliente=cliente,
            factura="FAC-001",
            embarque="E1",
            dia_embarque=1,
            fecha="2025-01-01",
            mes="Enero"
        )

        # 3. Agregar Detalle (Dispara señal)
        DetalleVenta.objects.create(
            venta=venta,
            producto="Queso",
            cantidad=10,
            precio_unitario=5.00,
            precio_total=50.00
        )
        
        venta.refresh_from_db()
        assert venta.total == 50.00
        assert venta.saldo == 50.00

        # 4. Registrar Pago Parcial (Dispara señal)
        Pago.objects.create(
            venta=venta,
            fecha="2025-01-02",
            monto=20.00
        )

        venta.refresh_from_db()
        assert venta.abono == 20.00
        assert venta.saldo == 30.00
        assert venta.estado == "PARCIAL"

    def test_seguridad_vistas_protegidas(self, client):
        # Intentar acceder a lista de clientes sin login
        url = reverse("clientes:cliente_list")
        response = client.get(url)
        # Debe redirigir al login (302)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    @patch("modulo_ia.gemini_service.genai.Client")
    def test_ia_analisis_mock(self, mock_genai, client_auth):
        # Mockear respuesta de Gemini
        mock_instance = mock_genai.return_value
        mock_instance.models.generate_content.return_value.text = "Recomendación: Cobrar inmediato."
        
        url = reverse("ia_analizar") # Corregido al nombre real
        payload = {"data": "cliente con deuda de 30 USD", "complexity": "standard"}
        
        response = client_auth.post(url, data=payload, content_type="application/json")
        
        assert response.status_code == 200
        assert "Recomendación" in response.json()["result"]
