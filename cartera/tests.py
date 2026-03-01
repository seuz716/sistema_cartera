from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from clientes.models import Cliente
from productos.models import Producto
from ventas.models import Venta, DetalleVenta
from .models import Pago

class PagoModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(nombre="Test Cliente", numero_identificacion="123")
        self.producto = Producto.objects.create(nombre="Test Producto", precio_unitario=Decimal("100.00"), stock_actual=10)
        self.venta = Venta.objects.create(factura="F-TEST-001", cliente=self.cliente, fecha="2024-03-01")
        self.detalle = DetalleVenta.objects.create(
            venta=self.venta, 
            producto=self.producto, 
            cantidad=Decimal("2"), 
            precio_unitario=Decimal("100.00")
        )
        self.venta.actualizar_totales() # total_con_flete = 200.00

    def test_crear_pago_actualiza_saldo_y_estado_parcial(self):
        """Un pago parcial debe cambiar el estado a PARCIAL y reducir el saldo."""
        pago = Pago.objects.create(
            venta=self.venta,
            fecha="2024-03-01",
            monto=Decimal("50.00"),
            metodo_pago="EFECTIVO"
        )
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.abono, Decimal("50.00"))
        self.assertEqual(self.venta.saldo, Decimal("150.00"))
        self.assertEqual(self.venta.estado, "PARCIAL")

    def test_pago_total_cambia_a_pagada(self):
        """Un pago que cubre el total debe cambiar el estado a PAGADA."""
        Pago.objects.create(
            venta=self.venta,
            fecha="2024-03-01",
            monto=Decimal("200.00"),
            metodo_pago="TRANSFERENCIA"
        )
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.saldo, Decimal("0.00"))
        self.assertEqual(self.venta.estado, "PAGADA")

    def test_pago_excesivo_bloqueado(self):
        """El modelo debe impedir pagos que superen el saldo pendiente."""
        with self.assertRaises(ValidationError):
            pago = Pago(
                venta=self.venta,
                fecha="2024-03-01",
                monto=Decimal("201.00")
            )
            pago.full_clean()
            pago.save()

    def test_pago_negativo_bloqueado(self):
        """El modelo debe impedir montos de pago de cero o negativos."""
        with self.assertRaises(ValidationError):
            pago = Pago(venta=self.venta, fecha="2024-03-01", monto=Decimal("-10.00"))
            pago.full_clean()
            pago.save()

    def test_borrar_pago_recalcula_saldo(self):
        """Al borrar un pago, el abono debe disminuir y el saldo aumentar."""
        pago = Pago.objects.create(venta=self.venta, fecha="2024-03-01", monto=Decimal("100.00"))
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.saldo, Decimal("100.00"))
        
        pago.delete()
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.abono, Decimal("0.00"))
        self.assertEqual(self.venta.saldo, Decimal("200.00"))
        self.assertEqual(self.venta.estado, "DEBE")

    def test_editar_pago_recalcula_saldo(self):
        """Al modificar el monto de un pago, el saldo de la venta debe actualizarse."""
        pago = Pago.objects.create(venta=self.venta, fecha="2024-03-01", monto=Decimal("50.00"))
        pago.monto = Decimal("150.00")
        pago.save()
        
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.saldo, Decimal("50.00"))

    def test_multiples_pagos(self):
        """Varios pagos deben sumarse correctamente en el abono."""
        Pago.objects.create(venta=self.venta, fecha="2024-03-01", monto=Decimal("50.00"))
        Pago.objects.create(venta=self.venta, fecha="2024-03-01", monto=Decimal("50.00"))
        
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.abono, Decimal("100.00"))
        self.assertEqual(self.venta.saldo, Decimal("100.00"))

    def test_estado_anulado_persiste(self):
        """Si una venta está ANULADA, el recalculo no debe cambiarle el estado a PAGADA o PARCIAL."""
        self.venta.estado = "ANULADA"
        self.venta.save()
        
        Pago.objects.create(venta=self.venta, fecha="2024-03-01", monto=Decimal("50.00"))
        self.venta.refresh_from_db()
        
        self.assertEqual(self.venta.estado, "ANULADA")
        self.assertEqual(self.venta.saldo, Decimal("150.00")) # El saldo sí actualiza, pero el estado no.
