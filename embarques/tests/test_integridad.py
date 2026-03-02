from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError

from embarques.models import (
    Embarque, Vehiculo, Transportador, Ruta, 
    TipoEmbalaje, CapacidadEmbalaje, EmbarqueCarga,
    TarifaTransporte
)
from productos.models import Producto
from clientes.models import Cliente
from ventas.models import Venta, DetalleVenta

class EmbarqueIntegrityTests(TestCase):
    def setUp(self):
        # 1. Configuración Base
        self.user = User.objects.create_user(username="testlogistics", password="pass")
        # Vehículo con capacidad de 1000kg
        self.vehiculo = Vehiculo.objects.create(placa="LOG-123", marca="Hino", capacidad_carga_kg=1000, activo=True)
        self.transportador = Transportador.objects.create(nombre="Carlos Trans", documento="111", activo=True)
        self.ruta = Ruta.objects.create(nombre="Cali - Manizales", ciudades_itinerario="Cali, Manizales")
        
        self.producto = Producto.objects.create(nombre="Queso Doble Crema", precio_unitario=10000, unidad_medida='UND')
        self.embalaje = TipoEmbalaje.objects.create(nombre="Canastilla", peso_vacio_kg=2.5)
        # 16 unidades por canastilla
        self.capacidad = CapacidadEmbalaje.objects.create(
            producto=self.producto, 
            tipo_embalaje=self.embalaje, 
            unidades_por_paquete=16
        )
        
        self.cliente = Cliente.objects.create(nombre="Tienda Juan", ciudad="Cali")

        # 2. Crear Embarque
        self.embarque = Embarque.objects.create(
            ruta=self.ruta,
            vehiculo=self.vehiculo,
            transportador=self.transportador,
            estado='PROGRAMADO',
            usuario_registro=self.user
        )

    # ==========================
    # 🔒 A. INTEGRIDAD DE ESTADO
    # ==========================

    def test_bloqueo_estado_finalizado(self):
        """1 & 2: No permitir modificar ni reabrir un embarque FINALIZADO."""
        self.embarque.estado = 'FINALIZADO'
        self.embarque.save()
        
        # Intentar modificar
        self.embarque.ruta = Ruta.objects.create(nombre="Ruta New")
        with self.assertRaises(ValidationError):
            self.embarque.save()
            
        # Intentar reabrir (de FINALIZADO a PROGRAMADO)
        self.embarque.estado = 'PROGRAMADO'
        with self.assertRaisesRegex(ValidationError, "No se puede reabrir"):
            self.embarque.clean()

    def test_bloqueo_carga_segun_estado(self):
        """3: No permitir modificar carga si estado ≠ PROGRAMADO o CARGANDO."""
        self.embarque.estado = 'EN_RUTA'
        self.embarque.save()
        
        carga = EmbarqueCarga(
            embarque=self.embarque, producto=self.producto, 
            tipo_embalaje=self.embalaje, cantidad_unidades=10
        )
        with self.assertRaisesRegex(ValidationError, "No se puede modificar la carga"):
            carga.save()

    # ==========================
    # 📦 B. INTEGRIDAD FÍSICA
    # ==========================

    def test_reconciliacion_inventario_exceso(self):
        """4 & 6: No permitir (entregado + devuelto) > cargado."""
        EmbarqueCarga.objects.create(
            embarque=self.embarque, producto=self.producto, tipo_embalaje=self.embalaje, cantidad_unidades=100
        )
        
        venta = Venta.objects.create(cliente=self.cliente, fecha=timezone.now().date(), embarque=self.embarque, confirmado=True)
        DetalleVenta.objects.create(venta=venta, producto=self.producto, unidades_entregadas=90, unidades_devueltas=15, cantidad_facturada=Decimal('90.00'), cantidad_devuelta_facturada=Decimal('15.00'), precio_unitario=10000)
        
        # 90 + 15 = 105 > 100
        with self.assertRaises(ValidationError):
            self.embarque.estado = 'FINALIZADO'
            self.embarque.clean()

    def test_reconciliacion_exacta(self):
        """5: Permitir entregar exactamente lo cargado."""
        EmbarqueCarga.objects.create(
            embarque=self.embarque, producto=self.producto, tipo_embalaje=self.embalaje, cantidad_unidades=100
        )
        venta = Venta.objects.create(cliente=self.cliente, fecha=timezone.now().date(), embarque=self.embarque, confirmado=True)
        DetalleVenta.objects.create(venta=venta, producto=self.producto, unidades_entregadas=100, unidades_devueltas=0, cantidad_facturada=Decimal('100.00'), cantidad_devuelta_facturada=Decimal('0.00'), precio_unitario=10000)
        
        # Debe pasar sin errores
        self.embarque.estado = 'FINALIZADO'
        self.embarque.clean()

    # ==========================
    # 📦 C. CAPACIDAD EMBALAJE
    # ==========================

    def test_calculo_paquetes(self):
        """7 & 9: cantidad_paquetes calcula correctamente (ej: 32 unidades -> 2 canastillas)."""
        carga = EmbarqueCarga.objects.create(
            embarque=self.embarque, producto=self.producto, tipo_embalaje=self.embalaje, cantidad_unidades=32
        )
        self.assertEqual(carga.cantidad_paquetes, 2)
        
        # Caso división no exacta (ej: 17 unidades en packs de 16 -> 2 paquetes)
        carga.cantidad_unidades = 17
        self.assertEqual(carga.cantidad_paquetes, 2)

    def test_paquetes_sin_capacidad(self):
        """8: Si no existe CapacidadEmbalaje -> devuelve 0 o maneja el error."""
        producto_nuevo = Producto.objects.create(nombre="Postre", precio_unitario=5000)
        carga = EmbarqueCarga.objects.create(
            embarque=self.embarque, producto=producto_nuevo, tipo_embalaje=self.embalaje, cantidad_unidades=10
        )
        # No hay capacidad_embalaje definida para Postre + Canastilla
        self.assertEqual(carga.cantidad_paquetes, 0)

    # ==========================
    # 🚛 D. CAPACIDAD VEHÍCULO
    # ==========================

    def test_sobrecarga_vehiculo(self):
        """10: No permitir pasar a EN_RUTA si peso total > capacidad_carga_kg."""
        # Cada unidad pesa 1kg (estimado) + canastilla 2.5kg.
        # Cargamos 1000 unidades -> 1000kg + 63 canastillas (1000/16 approx) * 2.5 = 1157.5 kg
        # El vehículo solo soporta 1000kg.
        EmbarqueCarga.objects.create(
            embarque=self.embarque, producto=self.producto, tipo_embalaje=self.embalaje, cantidad_unidades=1000
        )
        
        self.embarque.estado = 'EN_RUTA'
        with self.assertRaisesRegex(ValidationError, "SOBRECARGA"):
            self.embarque.clean()

    # ==========================
    # 💰 E. CÁLCULO FINANCIERO
    # ==========================

    def test_calculos_financieros_basicos(self):
        """11, 12, 13: Pago transportador, tarifa base y utilidad neta."""
        # Configurar tarifa transportador
        TarifaTransporte.objects.create(
            transportador=self.transportador, ruta=self.ruta, ciudad="Cali", 
            tipo_embalaje=self.embalaje, precio_por_embalaje=500
        )
        self.transportador.tarifa_base_viaje = 50000
        self.transportador.save()

        # Cargar 160 unidades (10 canastillas)
        EmbarqueCarga.objects.create(
            embarque=self.embarque, producto=self.producto, tipo_embalaje=self.embalaje, cantidad_unidades=160
        )

        # Simular ventas por $2,000,000
        # 160 unidades = 10 canastillas entregadas
        venta = Venta.objects.create(
            cliente=self.cliente, fecha=timezone.now().date(), 
            embarque=self.embarque, confirmado=True,
            total_embalajes_entregados=10
        )
        DetalleVenta.objects.create(venta=venta, producto=self.producto, unidades_entregadas=160, cantidad_facturada=Decimal('160.00'), precio_unitario=12500) # 160 * 12500 = 2M

        # Ejecutar cálculos (los modelos deben llamar a esto o el test lo fuerza)
        self.embarque.calcular_resultados()
        
        # Ingresos: 2,000,000
        # Pago Trans: 50,000 (base) + (10 canastillas * 500) = 55,000
        # Utilidad: 1,945,000
        self.assertEqual(self.embarque.ingresos_ventas, Decimal('2000000.00'))
        self.assertEqual(self.embarque.pago_transportador, Decimal('55000.00'))
        self.assertEqual(self.embarque.utilidad_neta, Decimal('1945000.00'))

    # ==========================
    # 🔄 F. CONSISTENCIA DE NÚMERO
    # ==========================

    def test_generacion_numero_embarque(self):
        """15 & 16: Generación automática y no duplicados (si aplica lógica de negocio)."""
        # Ya tenemos uno creado en setUp
        num1 = self.embarque.numero
        # num1 es un entero tipo ddmmyy01
        self.assertGreater(num1, 1000000) # Mínimo 7 dígitos
        
        # Crear otro el mismo día
        embarque2 = Embarque.objects.create(
            ruta=self.ruta, vehiculo=self.vehiculo, transportador=self.transportador, usuario_registro=self.user
        )
        self.assertEqual(embarque2.numero, num1 + 1)

    # ==========================
    # 📊 G. CIERRE OPERATIVO COMPLETO (TEST MAESTRO)
    # ==========================

    def test_flujo_maestro_logistica(self):
        """17: Simulación completa de un ciclo de vida de embarque."""
        # 1. PROGRAMADO: Cargar 160 unidades de Queso
        EmbarqueCarga.objects.create(
            embarque=self.embarque, producto=self.producto, tipo_embalaje=self.embalaje, cantidad_unidades=160
        )
        
        # 2. EN_RUTA: El vehículo sale
        self.embarque.estado = 'EN_RUTA'
        self.embarque.save()
        
        # 3. REGISTRAR VENTAS:
        # Venta 1: Entregadas 100 Unds, 0 devueltas. -> 100/16 = 6.25 -> 7 canastillas entregadas
        v1 = Venta.objects.create(
            cliente=self.cliente, fecha=timezone.now().date(), 
            embarque=self.embarque, confirmado=True, factura="F-001",
            total_embalajes_entregados=7
        )
        DetalleVenta.objects.create(venta=v1, producto=self.producto, unidades_entregadas=100, cantidad_facturada=Decimal('100.00'), precio_unitario=10000)
        
        # Venta 2: Entregadas 40 Unds, 10 devueltas. -> 40/16 = 2.5 -> 3 canastillas entregadas. 10/16 = 1 -> 1 devuelta
        v2 = Venta.objects.create(
            cliente=self.cliente, fecha=timezone.now().date(), 
            embarque=self.embarque, confirmado=True, factura="F-002",
            total_embalajes_entregados=3, total_embalajes_devueltos=1
        )
        DetalleVenta.objects.create(venta=v2, producto=self.producto, unidades_entregadas=40, unidades_devueltas=10, cantidad_facturada=Decimal('40.00'), cantidad_devuelta_facturada=Decimal('10.00'), precio_unitario=10000)
        
        # Total entregado: 140. Total devuelto: 10. Total reconciliado: 150.
        # Cargado 160. Quedan 10 unidades "en el carro" (stock volante) o pérdidas si se finaliza así.
        
        # 4. FINALIZAR:
        self.embarque.estado = 'FINALIZADO'
        self.embarque.save() # Llama a clean() -> calcular_resultados(commit=False) -> validar_cuadre_inventario()
        
        self.assertEqual(self.embarque.estado, 'FINALIZADO')
        # Verificar cálculos finales de canastillas (Persistentes)
        
        self.assertEqual(self.embarque.total_embalajes_enviados, 10)
        self.assertEqual(self.embarque.total_embalajes_entregados, 10)
        self.assertEqual(self.embarque.total_embalajes_devueltos, 1)
