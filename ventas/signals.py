from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from django.db import transaction

@receiver(post_save, sender='ventas.DetalleVenta')
def manejar_stock_y_totales_save(sender, instance, created, **kwargs):
    from .models import Venta
    from productos.models import Producto
    
    # 1. Actualizar Inventario
    if created and instance.producto.control_inventario:
        Producto.objects.filter(pk=instance.producto.pk).update(
            stock_actual=F('stock_actual') - instance.cantidad
        )
    
    # 2. Actualizar Totales de la Venta
    # Usamos transaction.on_commit para asegurar que el guardado del detalle terminó
    # o simplemente llamamos al método atómico
    instance.venta.actualizar_totales()

@receiver(post_delete, sender='ventas.DetalleVenta')
def manejar_stock_y_totales_delete(sender, instance, **kwargs):
    from productos.models import Producto
    
    # 1. Devolver Inventario
    if instance.producto.control_inventario:
        Producto.objects.filter(pk=instance.producto.pk).update(
            stock_actual=F('stock_actual') + instance.cantidad
        )
    
    # 2. Recalcular Totales
    instance.venta.actualizar_totales()

@receiver(post_save, sender='cartera.Pago')
def actualizar_venta_por_pago_save(sender, instance, created, **kwargs):
    if created:
        instance.venta.abono = F('abono') + instance.monto
        instance.venta.save()
        # Forzamos ejecución de lógica de saldos y estados
        instance.venta.refresh_from_db()
        instance.venta.actualizar_totales()

@receiver(post_delete, sender='cartera.Pago')
def actualizar_venta_por_pago_delete(sender, instance, **kwargs):
    instance.venta.abono = F('abono') - instance.monto
    instance.venta.save()
    instance.venta.refresh_from_db()
    instance.venta.actualizar_totales()
