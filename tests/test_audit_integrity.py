import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from productos.models import Producto, MovimientoInventario
from embarques.models import Embarque, EmbarqueItem, Ruta, Vehiculo, Transportador
from ventas.models import Venta, DetalleVenta
from cartera.models import ReciboCaja, Pago
from clientes.models import Cliente

@pytest.mark.django_db
class TestBusinessIntegrity:
    
    @pytest.fixture
    def setup_data(self, admin_user):
        # Setup basic infrastructure
        ruta = Ruta.objects.create(nombre="Ruta Norte")
        vehiculo = Vehiculo.objects.create(placa="XYZ-123", capacidad_carga_kg=5000)
        tra = Transportador.objects.create(nombre="Transportador 1", documento="123")
        prod = Producto.objects.create(
            nombre="Queso Audit", 
            tipo_medida="kg", 
            precio_unitario=Decimal("20000"),
            stock_actual=Decimal("0")
        )
        cli = Cliente.objects.create(
            nombre="Cesar", apellido="Audit", 
            email="cesar@audit.com", numero_identificacion="1010"
        )
        return {
            'ruta': ruta,
            'vehiculo': vehiculo,
            'transportador': tra,
            'producto': prod,
            'cliente': cli,
            'user': admin_user
        }

    def test_inventory_global_conservation(self, setup_data):
        """
        Validates: Compra(100) -> Embarque(40) -> Venta(15) -> Anulacion.
        Verification of Producto.stock_actual and EmbarqueItem.disponible.
        """
        p = setup_data['producto']
        
        # 1. Purchase
        MovimientoInventario.objects.create(
            producto=p, tipo='compra', cantidad_kg=Decimal("100"), descripcion="Entrada"
        )
        p.refresh_from_db()
        assert p.stock_actual == Decimal("100")
        
        # 2. Shipment
        emb = Embarque.objects.create(ruta=setup_data['ruta'], estado='borrador')
        ei = EmbarqueItem.objects.create(embarque=emb, producto=p, cantidad_kg=Decimal("40"))
        emb.confirmar_embarque()
        
        p.refresh_from_db()
        assert p.stock_actual == Decimal("60") 
        
        # 3. Sale
        v = Venta.objects.create(cliente=setup_data['cliente'], embarque=emb, fecha=emb.fecha)
        det = DetalleVenta.objects.create(
            venta=v, producto=p, cantidad_kg=Decimal("15"), 
            precio_unitario=Decimal("20000"), embarque_item=ei
        )
        
        ei.refresh_from_db()
        assert ei.cantidad_disponible_kg == Decimal("25")
        
        # 4. Annulment
        v.estado = 'ANULADA'
        v.save()
        
        ei.refresh_from_db()
        assert ei.cantidad_disponible_kg == Decimal("40")

    def test_portfolio_lifecycle(self, setup_data):
        """
        Validates: Sales -> RC -> Payments -> Balance 0.
        """
        cli = setup_data['cliente']
        p = setup_data['producto']
        emb = Embarque.objects.create(ruta=setup_data['ruta'], estado='transito')
        ei = EmbarqueItem.objects.create(embarque=emb, producto=p, cantidad_kg=Decimal("100"))
        ei.cantidad_disponible_kg = 100; ei.save()

        # Create two invoices
        v1 = Venta.objects.create(cliente=cli, embarque=emb, fecha=emb.fecha)
        DetalleVenta.objects.create(venta=v1, producto=p, cantidad_kg=Decimal("10"), precio_unitario=Decimal("20000"), embarque_item=ei)
        v1.actualizar_totales()

        v2 = Venta.objects.create(cliente=cli, embarque=emb, fecha=emb.fecha)
        DetalleVenta.objects.create(venta=v2, producto=p, cantidad_kg=Decimal("5"), precio_unitario=Decimal("20000"), embarque_item=ei)
        v2.actualizar_totales()

        cli.refresh_from_db()
        assert cli.saldo == Decimal("300000")

        # Create Recibo de Caja (FIFO)
        rc = ReciboCaja.objects.create(
            cliente=cli, fecha=emb.fecha, monto_total=Decimal("250000"), metodo_pago='EFECTIVO'
        )
        rc.registrar_y_distribuir(setup_data['user'])

        v1.refresh_from_db()
        v2.refresh_from_db()
        cli.refresh_from_db()

        assert v1.estado == 'PAGADA'
        assert v2.estado == 'PARCIAL'
        assert cli.saldo == Decimal("50000")

    def test_negative_inventory_block(self, setup_data):
        """
        Ensures system blocks sales exceeding available stock.
        """
        p = setup_data['producto']
        emb = Embarque.objects.create(ruta=setup_data['ruta'], estado='transito')
        ei = EmbarqueItem.objects.create(embarque=emb, producto=p, cantidad_kg=Decimal("10"))
        ei.cantidad_disponible_kg = 10; ei.save()

        v = Venta.objects.create(cliente=setup_data['cliente'], embarque=emb, fecha=emb.fecha)
        with pytest.raises(ValidationError) as exc:
            DetalleVenta.objects.create(
                venta=v, producto=p, cantidad_kg=Decimal("11"), 
                precio_unitario=Decimal("1000"), embarque_item=ei
            )
        assert "Stock insuficiente" in str(exc.value)

    def test_over_payment_block(self, setup_data):
        """
        Ensures a payment cannot exceed the invoice balance.
        """
        cli = setup_data['cliente']
        p = setup_data['producto']
        emb = Embarque.objects.create(ruta=setup_data['ruta'], estado='transito')
        v = Venta.objects.create(cliente=cli, embarque=emb, fecha=emb.fecha)
        DetalleVenta.objects.create(venta=v, producto=p, cantidad_kg=5, precio_unitario=1000)
        v.actualizar_totales()

        with pytest.raises(ValidationError) as exc:
            Pago.objects.create(
                venta=v, monto=Decimal("5001"), fecha=v.fecha, 
                usuario_registro=setup_data['user']
            )
        assert "excede el saldo pendiente" in str(exc.value)

    def test_annulment_clears_cartera(self, setup_data):
        """
        Validates that an annulled invoice results in 0 balance for the client.
        """
        cli = setup_data['cliente']
        emb = Embarque.objects.create(ruta=setup_data['ruta'], estado='transito')
        v = Venta.objects.create(cliente=cli, embarque=emb, fecha=emb.fecha)
        DetalleVenta.objects.create(venta=v, producto=setup_data['producto'], cantidad_kg=5, precio_unitario=1000)
        v.actualizar_totales()
        cli.refresh_from_db()
        assert cli.saldo == Decimal("5000")

        v.estado = 'ANULADA'
        v.save()
        # cli recalcula via signal
        cli.refresh_from_db()
        assert cli.saldo == 0

    def test_global_inventory_conservation_law(self, setup_data):
        """
        Verify that: Total Intake = Physical + Transit + Sold + Novedades.
        """
        from django.db.models import Sum
        p = setup_data['producto']
        
        # 1. Buy 1000kg
        MovimientoInventario.objects.create(producto=p, tipo='compra', cantidad_kg=1000)
        
        # 2. Ship 300kg (Shipment A)
        embA = Embarque.objects.create(ruta=setup_data['ruta'], estado='borrador')
        eiA = EmbarqueItem.objects.create(embarque=embA, producto=p, cantidad_kg=300)
        embA.confirmar_embarque()
        
        # 3. Ship 200kg (Shipment B)
        embB = Embarque.objects.create(ruta=setup_data['ruta'], estado='borrador')
        eiB = EmbarqueItem.objects.create(embarque=embB, producto=p, cantidad_kg=200)
        embB.confirmar_embarque()
        
        # Stock Current in warehouse should be 500
        p.refresh_from_db()
        assert p.stock_actual == 500
        
        # 4. Sell 100kg from A
        vA = Venta.objects.create(cliente=setup_data['cliente'], embarque=embA, fecha=embA.fecha)
        DetalleVenta.objects.create(venta=vA, producto=p, cantidad_kg=100, precio_unitario=10, embarque_item=eiA)
        
        # 5. Sell 50kg from B
        vB = Venta.objects.create(cliente=setup_data['cliente'], embarque=embB, fecha=embB.fecha)
        DetalleVenta.objects.create(venta=vB, producto=p, cantidad_kg=50, precio_unitario=10, embarque_item=eiB)
        
        # 6. Record 10kg Waste in Shipment A
        from embarques.models import NovedadEmbarque
        NovedadEmbarque.objects.create(embarque=embA, producto=p, tipo='ajuste_merma', cantidad_kg=10)
        
        # --- CONSERVATION CHECK ---
        physical = p.stock_actual # 500
        
        # Transit = sum of available in active shipments
        transit = EmbarqueItem.objects.filter(producto=p, embarque__estado='transito').aggregate(total=Sum('cantidad_disponible_kg'))['total'] or 0
        # A: 300 - 100 - 10 = 190
        # B: 200 - 50 = 150
        # Total Transit: 340
        
        # Sold = sum of DetalleVenta
        sold = DetalleVenta.objects.filter(producto=p, venta__estado__in=['BORRADOR', 'DEBE', 'PARCIAL', 'PAGADA', 'FINALIZADA']).aggregate(total=Sum('cantidad_kg'))['total'] or 0
        # 100 + 50 = 150
        
        # Waste/Novedades (Negative movements in transit)
        waste = NovedadEmbarque.objects.filter(producto=p, tipo__in=['ajuste_merma', 'daño', 'ajuste_diferencia']).aggregate(total=Sum('cantidad_kg'))['total'] or 0
        # 10
        
        total_recon = physical + transit + sold + waste
        assert total_recon == Decimal("1000")
