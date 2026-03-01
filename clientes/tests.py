from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Cliente
from ventas.models import Venta, DetalleVenta
from productos.models import Producto

class ClienteModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            numero_identificacion="123456789",
            tipo_persona="natural",
            nombre="Cesar",
            apellido="Abadia",
            email="cesar@example.com",
            ciudad="Quito",
            forma_pago="credito_30"
        )
        self.producto = Producto.objects.create(
            nombre="Queso",
            precio_unitario=Decimal("10.00")
        )

    def test_identificacion_unica(self):
        """No se puede crear otro cliente con la misma identificación."""
        with self.assertRaises(Exception): # IntegrityError
            Cliente.objects.create(
                numero_identificacion="123456789",
                nombre="Otro",
                apellido="Cualquiera",
                email="otro@example.com"
            )

    def test_email_unico(self):
        """No se puede crear otro cliente con el mismo email."""
        with self.assertRaises(Exception):
            Cliente.objects.create(
                numero_identificacion="987654321",
                nombre="Maria",
                apellido="Lopez",
                email="cesar@example.com"
            )

    def test_saldo_sincronizado_con_ventas(self):
        """El saldo del cliente debe subir automáticamente al crear una venta."""
        venta = Venta.objects.create(
            factura="F-SYNC-001",
            cliente=self.cliente,
            fecha="2024-03-01"
        )
        DetalleVenta.objects.create(
            venta=venta,
            producto=self.producto,
            cantidad=Decimal("5"),
            precio_unitario=Decimal("10.00")
        )
        # La señal de DetalleVenta llama a venta.actualizar_totales()
        # Y la señal de Venta llama a cliente.recalcular_saldo()
        
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.saldo, Decimal("50.00"))

    def test_saldo_sincronizado_con_anulacion(self):
        """El saldo del cliente debe bajar a 0 si se anula la única factura."""
        venta = Venta.objects.create(factura="F-SYNC-002", cliente=self.cliente, fecha="2024-03-01")
        DetalleVenta.objects.create(venta=venta, producto=self.producto, cantidad=Decimal("1"), precio_unitario=Decimal("10.00"))
        
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.saldo, Decimal("10.00"))
        
        venta.estado = "ANULADA"
        venta.save()
        
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.saldo, Decimal("0.00"))


from django.urls import reverse
from django.contrib.auth.models import User

class ClienteCRUDTest(TestCase):
    def setUp(self):
        # Creamos un usuario para las pruebas de login_required
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')
        
        self.cliente = Cliente.objects.create(
            numero_identificacion="101010",
            tipo_persona="natural",
            nombre="Juan",
            apellido="Prueba",
            email="juan@test.com",
            ciudad="Ambato",
            forma_pago="contado"
        )

    def test_view_cliente_list(self):
        response = self.client.get(reverse('clientes:cliente_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan")

    def test_view_cliente_detail(self):
        response = self.client.get(reverse('clientes:cliente_detail', args=[self.cliente.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan Prueba")

    def test_view_cliente_create(self):
        data = {
            'numero_identificacion': "202020",
            'tipo_persona': "juridica",
            'nombre': "Empresa",
            'apellido': "S.A.",
            'email': "empresa@test.com",
            'ciudad': "Quito",
            'forma_pago': "credito_15",
            'activo': True
        }
        response = self.client.post(reverse('clientes:cliente_create'), data)
        self.assertEqual(response.status_code, 302) # Redirección tras éxito
        self.assertTrue(Cliente.objects.filter(numero_identificacion="202020").exists())

    def test_view_cliente_update(self):
        data = {
            'numero_identificacion': "101010", # Mantenemos id
            'tipo_persona': "natural",
            'nombre': "Juan Editado",
            'apellido': "Prueba",
            'email': "juan@test.com",
            'ciudad': "Ambato",
            'forma_pago': "contado",
            'activo': True
        }
        response = self.client.post(reverse('clientes:cliente_update', args=[self.cliente.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, "Juan Editado")

    def test_view_cliente_delete(self):
        # El delete suele pedir confirmación por GET y borrar por POST
        response = self.client.post(reverse('clientes:cliente_delete', args=[self.cliente.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cliente.objects.filter(pk=self.cliente.pk).exists())
