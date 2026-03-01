import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from clientes.models import Cliente
from productos.models import Producto
from ventas.models import Venta, DetalleVenta
from cartera.models import Pago
from decimal import Decimal

@pytest.mark.django_db
class TestVentasYCartera:

    @pytest.fixture
    def setup_data(self):
        user = User.objects.create_user(username="admin", password="password")
        cliente = Cliente.objects.create(
            numero_identificacion="1312345678",
            nombre="Juan",
            apellido="Perez",
            tipo_persona="natural",
            email="juan@example.com",
            forma_pago="contado"
        )
        producto = Producto.objects.create(
            nombre="Queso Manabita",
            precio_unitario=5.00,
            stock_actual=100,
            control_inventario=True
        )
        return user, cliente, producto

    def test_creacion_venta_y_stock(self, client, setup_data):
        user, cliente, producto = setup_data
        client.login(username="admin", password="password")
        
        # 1. Crear Venta
        venta = Venta.objects.create(
            factura="F-001",
            cliente=cliente,
            fecha="2024-03-01",
            flete=Decimal("10.00")
        )
        
        # 2. Agregar Detalle (Debería disparar señal para restar stock)
        detalle = DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=Decimal("10.00"),
            precio_unitario=Decimal("5.00")
        )
        
        # Verificar cálculos
        venta.refresh_from_db()
        # subtotal = 10 * 5 = 50
        # total_con_flete = 50 + 10 = 60
        assert venta.subtotal == Decimal("50.00")
        assert venta.total_con_flete == Decimal("60.00")
        assert venta.saldo == Decimal("60.00")
        assert venta.estado == "DEBE"
        
        # Verificar stock
        producto.refresh_from_db()
        assert producto.stock_actual == Decimal("90.00")

    def test_pago_actualiza_saldo_y_estado(self, client, setup_data):
        user, cliente, producto = setup_data
        venta = Venta.objects.create(
            factura="F-002",
            cliente=cliente,
            fecha="2024-03-01"
        )
        DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=Decimal("2"),
            precio_unitario=Decimal("10.00")
        )
        # Total = 20.00
        
        # Registrar Pago Parcial
        Pago.objects.create(
            venta=venta,
            fecha="2024-03-01",
            monto=Decimal("15.00"),
            metodo_pago='EFECTIVO'
        )
        
        venta.refresh_from_db()
        assert venta.abono == Decimal("15.00")
        assert venta.saldo == Decimal("5.00")
        assert venta.estado == "PARCIAL"
        
        # Registrar Pago restante
        Pago.objects.create(
            venta=venta,
            fecha="2024-03-02",
            monto=Decimal("5.00")
        )
        
        venta.refresh_from_db()
        assert venta.saldo == Decimal("0.00")
        assert venta.estado == "PAGADA"

    def test_acceso_denegado_sin_login(self, client):
        """Verifica que las vistas críticas redirijan al login."""
        urls = [
            reverse('ventas:lista'),
            reverse('ventas:crear'),
            reverse('cartera:lista'),
            reverse('cartera:crear'),
            reverse('home'),
        ]
        for url in urls:
            response = client.get(url)
            assert response.status_code == 302
            assert "/accounts/login/" in response.url

    def test_listado_ventas_select_related(self, client, setup_data):
        """Verifica que el listado de ventas funcione con login."""
        user, cliente, producto = setup_data
        client.login(username="admin", password="password")
        
        venta = Venta.objects.create(factura="F-LIST", cliente=cliente, fecha="2024-03-01", flete=Decimal("100.00"))
        venta.actualizar_totales() # Asegura saldo > 0
        
        url = reverse('ventas:lista')
        response = client.get(url)
        assert response.status_code == 200
        assert "F-LIST" in response.content.decode()
