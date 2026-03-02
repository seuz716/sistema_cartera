from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import transaction

from ventas.models import Venta, DetalleVenta, ConfiguracionFactura
from clientes.models import Cliente
from embarques.models import Embarque, Vehiculo, Transportador, Ruta
from productos.models import Producto

class VentaSecurityTests(TestCase):
    """
    Verifica que todas las vistas estén protegidas por autenticación.
    """
    def setUp(self):
        self.client = Client()
        # Mock objects for detail/json views
        self.cliente = Cliente.objects.create(nombre="Test", apellido="User", email="test@test.com")
        self.vehiculo = Vehiculo.objects.create(placa="TTT-000")
        self.transportador = Transportador.objects.create(nombre="Trans", documento="123")
        self.ruta = Ruta.objects.create(nombre="Ruta Test")
        self.embarque = Embarque.objects.create(ruta=self.ruta, vehiculo=self.vehiculo, transportador=self.transportador)
        self.venta = Venta.objects.create(cliente=self.cliente, fecha="2026-03-02", embarque=self.embarque)

    def test_list_requires_login(self):
        response = self.client.get(reverse('ventas:lista'))
        self.assertEqual(response.status_code, 302)

    def test_detail_requires_login(self):
        response = self.client.get(reverse('ventas:detalle', args=[self.venta.pk]))
        self.assertEqual(response.status_code, 302)

    def test_create_requires_login(self):
        response = self.client.get(reverse('ventas:crear'))
        self.assertEqual(response.status_code, 302)

    def test_json_requires_login(self):
        response = self.client.get(reverse('ventas:embarque_conductor', args=[self.embarque.pk]))
        self.assertEqual(response.status_code, 302)

class VentaCreateTests(TestCase):
    """
    Pruebas de creación de venta y validaciones financieras.
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')

        self.cliente = Cliente.objects.create(nombre="Juan", apellido="Perez", email="juan@perez.com")
        self.producto = Producto.objects.create(nombre="Producto Test", precio_unitario=10000)

        # Configuración obligatoria
        ConfiguracionFactura.objects.create(pk=1, prefijo="FV", numero_inicio=1)
        self.vehiculo = Vehiculo.objects.create(placa="C-TEST")
        self.transportador = Transportador.objects.create(nombre="Trans", documento="111")
        self.ruta = Ruta.objects.create(nombre="Ruta Test")
        self.embarque = Embarque.objects.create(ruta=self.ruta, vehiculo=self.vehiculo, transportador=self.transportador, estado='PROGRAMADO')

    def test_crear_venta_exitosa(self):
        """
        Debe crear venta, detalles y calcular totales correctamente.
        """
        data = {
            'cliente': self.cliente.pk,
            'fecha': '2026-03-02',
            'embarque': self.embarque.pk,
            'conductor': 'Test',
            'total_embalajes_entregados': '5',
            'total_embalajes_devueltos': '0',
            'descuentos': 0,
            'flete': 1000,
            'detalles-TOTAL_FORMS': '1',
            'detalles-INITIAL_FORMS': '0',
            'detalles-MIN_NUM_FORMS': '0',
            'detalles-MAX_NUM_FORMS': '1000',
            'detalles-0-producto': self.producto.pk,
            'detalles-0-unidades_entregadas': '2',
            'detalles-0-cantidad_facturada': '2',
            'detalles-0-precio_unitario': '10000',
        }

        response = self.client.post(reverse('ventas:crear'), data)
        # Check for success redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Venta.objects.count(), 1)

        venta = Venta.objects.first()
        self.assertEqual(venta.subtotal, Decimal('20000'))
        # Total = 20000 (subtotal) - 0 (desc) - 1000 (flete) = 19000
        self.assertEqual(venta.total_con_flete, Decimal('19000'))

    def test_descuento_mayor_que_subtotal(self):
        """
        No debe permitir descuentos mayores al subtotal.
        """
        data = {
            'cliente': self.cliente.pk,
            'fecha': '2026-03-02',
            'embarque': self.embarque.pk,
            'conductor': 'Test',
            'total_embalajes_entregados': '5',
            'total_embalajes_devueltos': '0',
            'descuentos': 50000,
            'flete': 0,
            'detalles-TOTAL_FORMS': '1',
            'detalles-INITIAL_FORMS': '0',
            'detalles-MIN_NUM_FORMS': '0',
            'detalles-MAX_NUM_FORMS': '1000',
            'detalles-0-producto': self.producto.pk,
            'detalles-0-unidades_entregadas': '1',
            'detalles-0-cantidad_facturada': '1',
            'detalles-0-precio_unitario': '10000',
        }

        response = self.client.post(reverse('ventas:crear'), data)
        self.assertEqual(Venta.objects.count(), 0)
        self.assertContains(response, "no pueden ser mayores")

    def test_atomic_rollback_si_error(self):
        """
        Si ocurre error dentro de atomic(), no debe guardarse venta parcial.
        """
        data = {
            'cliente': self.cliente.pk,
            'fecha': '2026-03-02',
            'embarque': self.embarque.pk,
            'conductor': 'Test',
            'total_embalajes_entregados': '5',
            'total_embalajes_devueltos': '0',
            'descuentos': 0,
            'flete': 0,
            'detalles-TOTAL_FORMS': '1',
            'detalles-INITIAL_FORMS': '0',
            'detalles-MIN_NUM_FORMS': '0',
            'detalles-MAX_NUM_FORMS': '1000',
            'detalles-0-producto': self.producto.pk,
            'detalles-0-unidades_entregadas': '1',
            'detalles-0-cantidad_facturada': '1',
            'detalles-0-precio_unitario': '10000',
        }

        # Forzamos error eliminando configuración para romper consecutivo
        ConfiguracionFactura.objects.all().delete()

        # In case of redirect, it means it didn't fail at generating consecutivo in the POST logic?
        # Actually it redirects back OR fails inside the transaction.
        response = self.client.post(reverse('ventas:crear'), data)
        self.assertEqual(Venta.objects.count(), 0)

class VentaListTests(TestCase):
    """
    Verifica filtros y agregados de listados.
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testview', password='password123')
        self.client.login(username='testview', password='password123')

        self.cliente = Cliente.objects.create(nombre="Juan", apellido="Perez", email="juan@view.com")
        self.vehiculo = Vehiculo.objects.create(placa="VVV-000")
        self.transportador = Transportador.objects.create(nombre="Trans", documento="123")
        self.ruta = Ruta.objects.create(nombre="Ruta Venta")
        self.embarque = Embarque.objects.create(
            ruta=self.ruta, vehiculo=self.vehiculo, transportador=self.transportador,
            estado='EN_RUTA',
            conductor='Carlos'
        )
        # We need distinct facturas or they will fail unique constraint if using default
        self.venta1 = Venta.objects.create(cliente=self.cliente, fecha="2026-03-01", factura="FV1", saldo=1000, embarque=self.embarque)
        self.venta2 = Venta.objects.create(cliente=self.cliente, fecha="2026-03-02", factura="FV2", saldo=2000, embarque=self.embarque)
        self.venta_pagada = Venta.objects.create(cliente=self.cliente, fecha="2026-03-03", factura="FV3", saldo=0, embarque=self.embarque)

    def test_lista_solo_muestra_con_saldo(self):
        response = self.client.get(reverse('ventas:lista'))
        self.assertContains(response, "FV1")
        self.assertContains(response, "FV2")
        self.assertNotContains(response, "FV3")

    def test_total_saldo_calculado(self):
        response = self.client.get(reverse('ventas:lista'))
        self.assertEqual(response.context['total_saldo'], Decimal('3000'))

class EmbarqueJsonTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testjson', password='password123')
        self.client.login(username='testjson', password='password123')

        self.vehiculo = Vehiculo.objects.create(placa="ABC123", marca="Camión", modelo="Z1")
        self.transportador = Transportador.objects.create(nombre="Carlos", documento="123")
        self.ruta = Ruta.objects.create(nombre="Ruta Test")
        self.embarque = Embarque.objects.create(
            ruta=self.ruta,
            vehiculo=self.vehiculo,
            transportador=self.transportador,
            conductor='Carlos'
        )

    def test_json_devuelve_datos_correctos(self):
        response = self.client.get(
            reverse('ventas:embarque_conductor', args=[self.embarque.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'conductor': 'Carlos',
            'vehiculo': 'Camión Z1 (ABC123)',
            'placa': 'ABC123',
        })

    def test_json_404_si_no_existe(self):
        response = self.client.get(reverse('ventas:embarque_conductor', args=[999]))
        self.assertEqual(response.status_code, 404)

class ConfiguracionFacturaTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='admin_config', password='password123')
        self.client.login(username='admin_config', password='password123')

    def test_crea_configuracion(self):
        response = self.client.post(reverse('ventas:configurar_facturas'), {
            'prefijo': 'FAC',
            'numero_inicio': 100
        })
        # Check for success redirect to create view
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ConfiguracionFactura.objects.count(), 1)
        config = ConfiguracionFactura.objects.first()
        self.assertEqual(config.prefijo, 'FAC')
        self.assertEqual(config.numero_inicio, 100)
