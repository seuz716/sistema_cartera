from decimal import Decimal
from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection, transaction

from clientes.models import Cliente
from productos.models import Producto
from ventas.models import Venta, DetalleVenta
from cartera.models import Pago
from embarques.models import Embarque, Vehiculo, Transportador, Ruta

class PagoValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='admin_pago', password='password123')
        self.client.login(username='admin_pago', password='password123')

        self.cliente = Cliente.objects.create(nombre="Juan", apellido="Perez", numero_identificacion="998877")
        self.producto = Producto.objects.create(nombre="Test Prod", precio_unitario=Decimal("100000"))
        self.vehiculo = Vehiculo.objects.create(placa="CARTERA-1")
        self.transportador = Transportador.objects.create(nombre="Trans", documento="123")
        self.ruta = Ruta.objects.create(nombre="Ruta Test")
        self.embarque = Embarque.objects.create(ruta=self.ruta, vehiculo=self.vehiculo, transportador=self.transportador, usuario_registro=self.user)
        
        self.venta = Venta.objects.create(cliente=self.cliente, fecha="2026-03-01", factura="FV-P1", embarque=self.embarque)
        DetalleVenta.objects.create(venta=self.venta, producto=self.producto, unidades_entregadas=1, cantidad_facturada=1, precio_unitario=100000)
        self.venta.actualizar_totales() # Total: 100.000

    def test_pago_duplicado_misma_venta_fecha_referencia(self):
        """No debe permitir dos pagos con misma referencia en la misma fecha para la misma venta."""
        Pago.objects.create(
            venta=self.venta,
            fecha="2026-03-02",
            monto=Decimal("50000"),
            referencia="REF-123"
        )

        with self.assertRaises(ValidationError):
            pago = Pago(
                venta=self.venta,
                fecha="2026-03-02",
                monto=Decimal("10000"),
                referencia="REF-123"
            )
            pago.full_clean()
            pago.save()

    def test_pago_misma_referencia_diferente_fecha_permitido(self):
        """Debe permitir misma referencia si la fecha es diferente."""
        Pago.objects.create(
            venta=self.venta,
            fecha="2026-03-01",
            monto=Decimal("10000"),
            referencia="REF-123"
        )

        # Diferente día, misma referencia
        pago = Pago.objects.create(
            venta=self.venta,
            fecha="2026-03-02",
            monto=Decimal("10000"),
            referencia="REF-123"
        )
        self.assertEqual(Pago.objects.count(), 2)

    def test_pago_duplicado_mismo_cliente_misma_fecha_referencia(self):
        """No debe permitir duplicado por cliente aunque sea otra venta."""
        otra_venta = Venta.objects.create(cliente=self.cliente, fecha="2026-03-01", factura="FV-P2", embarque=self.embarque)
        DetalleVenta.objects.create(venta=otra_venta, producto=self.producto, unidades_entregadas=1, cantidad_facturada=1, precio_unitario=100000)
        otra_venta.actualizar_totales()

        Pago.objects.create(
            venta=self.venta,
            fecha="2026-03-02",
            monto=Decimal("10000"),
            referencia="REF-DUP",
            usuario_registro=self.user
        )

        with self.assertRaises(ValidationError):
            pago = Pago(
                venta=otra_venta,
                fecha="2026-03-02",
                monto=Decimal("10000"),
                referencia="REF-DUP",
                usuario_registro=self.user
            )
            pago.full_clean()
            pago.save()

    def test_pago_sin_referencia_no_bloquea(self):
        """Pagos sin referencia no deben bloquearse entre sí."""
        Pago.objects.create(
            venta=self.venta,
            fecha="2026-03-02",
            monto=Decimal("10000"),
            referencia=None,
            usuario_registro=self.user
        )

        # Otro pago sin referencia el mismo día
        pago = Pago.objects.create(
            venta=self.venta,
            fecha="2026-03-02",
            monto=Decimal("10000"),
            referencia=None,
            usuario_registro=self.user
        )
        self.assertEqual(Pago.objects.count(), 2)

    def test_pago_monto_superior_saldo_bloqueado(self):
        """No debe permitir pagos que superen el saldo actual de la venta."""
        with self.assertRaises(ValidationError):
            pago = Pago(
                venta=self.venta,
                fecha="2026-03-02",
                monto=Decimal("100001"), # Excede los 100.000
                usuario_registro=self.user
            )
            pago.full_clean()
            pago.save()

    # =========================
    # 🏦 PRUEBAS NIVEL BANCO
    # =========================

    def test_referencia_normalizacion(self):
        """La referencia debe normalizarse a mayúsculas y sin espacios (Bank Standard)."""
        pago = Pago.objects.create(
            venta=self.venta,
            fecha="2026-03-02",
            monto=Decimal("1000"),
            referencia="   ref-abc-123   ",
            usuario_registro=self.user
        )
        self.assertEqual(pago.referencia, "REF-ABC-123")

    def test_pago_inmutable(self):
        """Un pago confirmado (guardado) no debe permitir edición."""
        pago = Pago.objects.create(
            venta=self.venta,
            fecha="2026-03-02",
            monto=Decimal("1000"),
            referencia="REF-IMM",
            usuario_registro=self.user
        )
        
        pago.monto = Decimal("2000")
        with self.assertRaises(ValidationError) as cm:
            pago.full_clean()
        
        self.assertIn("inmutables", str(cm.exception))

    def test_hash_integridad_generado(self):
        """Cada pago debe generar un hash SHA256 de integridad."""
        pago = Pago.objects.create(
            venta=self.venta,
            fecha="2026-03-02",
            monto=Decimal("5000"),
            referencia="HASH-TEST",
            usuario_registro=self.user
        )
        self.assertTrue(len(pago.hash_integridad) == 64)
        self.assertIsNotNone(pago.hash_integridad)

class PagoConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bank_officer', password='password123')
        self.cliente = Cliente.objects.create(nombre="Bank", apellido="Client", numero_identificacion="112233")
        self.producto = Producto.objects.create(nombre="Gold", precio_unitario=Decimal("1000000"))
        self.vehiculo = Vehiculo.objects.create(placa="C-BANK")
        self.transportador = Transportador.objects.create(nombre="Trans-B", documento="456")
        self.ruta = Ruta.objects.create(nombre="Ruta B")
        self.embarque = Embarque.objects.create(ruta=self.ruta, vehiculo=self.vehiculo, transportador=self.transportador, usuario_registro=self.user)
        self.venta = Venta.objects.create(cliente=self.cliente, fecha="2026-03-01", factura="BANK-1", embarque=self.embarque)
        DetalleVenta.objects.create(venta=self.venta, producto=self.producto, unidades_entregadas=1, cantidad_facturada=1, precio_unitario=1000000)
        self.venta.actualizar_totales()

    def test_concurrencia_unique_constraint(self):
        """Simulamos concurrencia para verificar que el UniqueConstraint de DB protege duplicados."""
        import threading

        def crear_pago():
            # En TransactionTestCase, cada hilo necesita su propia transacción
            # pero el constraint de la DB es el que manda.
            try:
                with transaction.atomic():
                    Pago.objects.create(
                        venta=self.venta,
                        fecha="2026-03-05",
                        monto=Decimal("1000"),
                        referencia="REF-CONC",
                        usuario_registro=self.user
                    )
            except Exception:
                # Esperamos que uno de los dos falle por el UniqueConstraint
                pass

        t1 = threading.Thread(target=crear_pago)
        t2 = threading.Thread(target=crear_pago)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Solo debe existir 1 pago con esa referencia
        count = Pago.objects.filter(referencia="REF-CONC").count()
        self.assertEqual(count, 1)
