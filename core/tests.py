from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from clientes.models import Cliente
from ventas.models import Venta, DetalleVenta
from productos.models import Producto
from cartera.models import Pago
from decimal import Decimal

class CoreDashboardTest(TestCase):
    def setUp(self):
        # Usuario para login
        self.user = User.objects.create_user(username='admin', password='password123')
        
        # Datos para poblar dashboard
        self.cliente = Cliente.objects.create(
            numero_identificacion="111", 
            nombre="Teo", 
            apellido="Core", 
            email="teo@core.com",
            ciudad="Quito"
        )
        self.producto = Producto.objects.create(nombre="Leche", precio_unitario=Decimal("2.00"))
        
        # Venta de 20.00
        self.venta = Venta.objects.create(factura="F-CORE-01", cliente=self.cliente, fecha="2024-03-01")
        DetalleVenta.objects.create(venta=self.venta, producto=self.producto, cantidad=Decimal("10"), precio_unitario=Decimal("2.00"))
        self.venta.actualizar_totales() # saldo = 20.00
        
        # Pago de 5.00
        Pago.objects.create(venta=self.venta, fecha="2024-03-01", monto=Decimal("5.00"))
        # Tras pago: saldo = 15.00, recaudado = 5.00

    def test_home_requires_login(self):
        """La página de inicio debe redirigir si no hay sesión."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_metrics(self):
        """Verifica que el dashboard sume correctamente los valores de otras apps."""
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_clientes'], 1)
        self.assertEqual(response.context['total_saldo'], Decimal("15.00"))
        self.assertEqual(response.context['total_recaudado'], Decimal("5.00"))

    def test_navigation_root_accessible(self):
        """Verifica que la URL raíz responda correctamente trás login."""
        self.client.login(username='admin', password='password123')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Panel de Control")
