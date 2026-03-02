from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError

from clientes.models import Cliente
from ventas.models import Venta

class ClienteTestCase(TestCase):

    def setUp(self):
        """
        Configuración base para todas las pruebas.
        """
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.cliente = Cliente.objects.create(
            numero_identificacion="123456",
            tipo_persona="natural",
            nombre="Juan",
            apellido="Pérez",
            email="juan@test.com",
            telefono="3000000000",
            direccion="Calle 123",
            ciudad="Bogotá",
            forma_pago="contado"
        )
        from embarques.models import Embarque
        self.embarque = Embarque.objects.create()

    # =========================
    # 🔐 PRUEBAS DE SEGURIDAD
    # =========================

    def test_cliente_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("clientes:cliente_list"))
        self.assertEqual(response.status_code, 302)

    def test_cliente_list_logged_in(self):
        response = self.client.get(reverse("clientes:cliente_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan")

    def test_cliente_detail_requires_login(self):
        self.client.logout()
        response = self.client.get(
            reverse("clientes:cliente_detail", args=[self.cliente.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_cliente_detail_404(self):
        response = self.client.get(
            reverse("clientes:cliente_detail", args=[9999])
        )
        self.assertEqual(response.status_code, 404)

    # =========================
    # ➕ PRUEBAS DE CREACIÓN
    # =========================

    def test_cliente_create_valid(self):
        data = {
            "numero_identificacion": "999999",
            "tipo_persona": "natural",
            "nombre": "Carlos",
            "apellido": "Lopez",
            "email": "carlos@test.com",
            "telefono": "3110000000",
            "direccion": "Calle 45",
            "ciudad": "Medellín",
            "forma_pago": "contado"
        }
        response = self.client.post(reverse("clientes:cliente_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Cliente.objects.count(), 2)

    def test_cliente_create_duplicate_email(self):
        data = {
            "numero_identificacion": "888888",
            "tipo_persona": "natural",
            "nombre": "Pedro",
            "apellido": "Gomez",
            "email": "juan@test.com",  # duplicado
            "ciudad": "Cali",
            "forma_pago": "contado"
        }
        response = self.client.post(reverse("clientes:cliente_create"), data)
        self.assertEqual(response.status_code, 200) # Re-renders form with errors
        self.assertEqual(Cliente.objects.count(), 1)

    # =========================
    # ✏️ PRUEBAS DE UPDATE
    # =========================

    def test_cliente_update_valid(self):
        data = {
            "numero_identificacion": "123456",
            "tipo_persona": "natural",
            "nombre": "Juan Actualizado",
            "apellido": "Pérez",
            "email": "juan@test.com",
            "telefono": "3000000000",
            "direccion": "Calle 123",
            "ciudad": "Bogotá",
            "forma_pago": "contado"
        }
        response = self.client.post(
            reverse("clientes:cliente_update", args=[self.cliente.pk]),
            data
        )
        self.assertEqual(response.status_code, 302)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, "Juan Actualizado")

    # =========================
    # 🗑 PRUEBAS DE DELETE
    # =========================

    def test_cliente_delete_post(self):
        response = self.client.post(
            reverse("clientes:cliente_delete", args=[self.cliente.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Cliente.objects.filter(pk=self.cliente.pk).count(), 0)

    # =========================
    # 💰 PRUEBAS DE MÉTODOS Y LÓGICA
    # =========================

    def test_nombre_completo(self):
        self.assertEqual(self.cliente.nombre_completo, "Juan Pérez")

    def test_recalcular_saldo_sin_ventas(self):
        self.cliente.recalcular_saldo()
        self.assertEqual(self.cliente.saldo, 0)

    def test_recalcular_saldo_con_ventas_reales(self):
        """
        Verifica que el saldo del cliente se actualice correctamente con ventas.
        """
        # Crear ventas
        Venta.objects.create(cliente=self.cliente, embarque=self.embarque, fecha="2026-03-01", factura="FV-T1", saldo=50000)
        Venta.objects.create(cliente=self.cliente, embarque=self.embarque, fecha="2026-03-02", factura="FV-T2", saldo=25000)
        # Venta anulada no debe contar
        Venta.objects.create(cliente=self.cliente, embarque=self.embarque, fecha="2026-03-03", factura="FV-T3", saldo=10000, estado='ANULADA')
        
        self.cliente.recalcular_saldo()
        self.assertEqual(self.cliente.saldo, Decimal('75000'))

    def test_forma_pago_otro_y_dias_credito(self):
        """
        Verifica el comportamiento de forma_pago='otro' (validación lógica).
        """
        self.cliente.forma_pago = "otro"
        self.cliente.dias_credito = 45
        self.cliente.save()
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.dias_credito, 45)

    def test_delete_cliente_con_ventas(self):
        """
        Verifica que no se pueda eliminar un cliente si tiene ventas (on_delete=PROTECT o confirmación).
        Actualmente el modelo Venta usa on_delete=CASCADE para cliente.
        Si queremos protegerlo, deberíamos cambiarlo.
        Por ahora testeamos el comportamiento actual (CASCADE).
        """
        Venta.objects.create(cliente=self.cliente, embarque=self.embarque, fecha="2026-03-02", factura="FV-T4")
        self.assertEqual(Venta.objects.count(), 1)
        
        self.cliente.delete()
        self.assertEqual(Cliente.objects.count(), 0)
        self.assertEqual(Venta.objects.count(), 0) # Cascade delete

    def test_campo_activo_soft_delete_logic(self):
        """
        Verifica que el campo activo funcione como bandera de soft delete.
        """
        self.cliente.activo = False
        self.cliente.save()
        self.assertFalse(Cliente.objects.get(pk=self.cliente.pk).activo)
