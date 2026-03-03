from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from django.db import transaction

@receiver(post_save, sender='ventas.DetalleVenta')
def manejar_stock_y_totales_save(sender, instance, created, **kwargs):
    from .models import Venta
    from productos.models import Producto
    
    # 1. Actualizar Inventario (Warehouse)
    # NOTA: En el nuevo modelo, la Venta descuenta del INVENTARIO EN TRÁNSITO del Embarque.
    # El stock del almacén (Producto.stock_actual) ya fue descontado al confirmar el embarque.
    pass
    
    # 2. Actualizar Totales de la Venta
    # Usamos transaction.on_commit para asegurar que el guardado del detalle terminó
    # o simplemente llamamos al método atómico
    instance.venta.actualizar_totales()

@receiver(post_delete, sender='ventas.DetalleVenta')
def manejar_stock_y_totales_delete(sender, instance, **kwargs):
    from productos.models import Producto
    
    # 1. Devolver Inventario (Warehouse)
    # NOTA: En el nuevo modelo, al eliminar un detalle de venta, el inventario debe retornar 
    # a la DISPONIBILIDAD del Embarque (esto se maneja en DetalleVenta.delete() o similar).
    # No afecta al stock_actual del almacén directamente.
    pass
    
    # 2. Recalcular Totales
    instance.venta.actualizar_totales()

@receiver(post_save, sender='cartera.Pago')
def actualizar_venta_por_pago_save(sender, instance, **kwargs):
    # Simplemente disparamos el recalculo completo para asegurar integridad
    instance.venta.actualizar_totales()

@receiver(post_delete, sender='cartera.Pago')
def actualizar_venta_por_pago_delete(sender, instance, **kwargs):
    # El objeto Pago ya no está en la DB, actualizar_totales lo ignorará al sumar
    instance.venta.actualizar_totales()

@receiver(post_save, sender='ventas.Venta')
def actualizar_cliente_saldo_save(sender, instance, **kwargs):
    """
    Cuando cambia cualquier dato de la venta (incluyendo el saldo recalclulado por señales),
    actualizamos el saldo total consolidado del cliente.
    """
    instance.cliente.recalcular_saldo()
