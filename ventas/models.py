from django.db import models
from clientes.models import Cliente
from productos.models import Producto


class Venta(models.Model):
    # Consecutivo interno sistema
    id_interno = models.AutoField(primary_key=True)
    # Número de factura visible (manual o auto)
    factura = models.CharField(max_length=50, unique=True, verbose_name="N° Factura")
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="ventas")
    
    fecha = models.DateField()
    embarque = models.CharField(max_length=50, blank=True, null=True)
    dia_embarque = models.PositiveIntegerField(blank=True, null=True)

    # Datos de transporte
    conductor = models.CharField(max_length=100, blank=True, null=True)
    flete = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Valores financieros globales
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuentos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_con_flete = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Cartera
    abono = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    ESTADO_CHOICES = [
        ('DEBE', 'Pendiente (Crédito)'),
        ('PAGADA', 'Pagada Totalmente'),
        ('PARCIAL', 'Abonada / Parcial'),
        ('ANULADA', 'Anulada'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='DEBE')

    notas = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Factura {self.factura} - {self.cliente}"

    def actualizar_totales(self) -> None:
        """
        Recalcula subtotal, total, abono y saldo a partir de los detalles y pagos
        relacionados, actualizando el estado de la factura (DEBE, PARCIAL, PAGADA).
        Usa select_for_update para prevenir race conditions.
        """
        # 1. Bloqueo de fila para evitar que otro proceso pise el saldo
        # Refrescamos desde la DB para tener valores exactos
        venta = Venta.objects.select_for_update().get(pk=self.pk)

        # 2. Totales de productos
        detalles = venta.detalles.all()
        subtotal = sum(det.precio_total for det in detalles)
        venta.subtotal = subtotal
        venta.total = subtotal - venta.descuentos
        venta.total_con_flete = venta.total - venta.flete

        # 3. Recalcular Abonos
        pagos = venta.pagos.all()
        venta.abono = sum(pago.monto for pago in pagos)

        # 4. Calcular Saldo Final
        venta.saldo = venta.total_con_flete - venta.abono
        
        # Guard clause: No sobreescribir si la factura está ANULADA
        if venta.estado != "ANULADA":
            if venta.saldo <= 0:
                venta.estado = "PAGADA"
            elif venta.abono > 0:
                venta.estado = "PARCIAL"
            else:
                venta.estado = "DEBE"
            
        # 5. Guardar cambios
        venta.save()
        
        # 6. Sincronizar el objeto actual en memoria por si acaso
        self.subtotal = venta.subtotal
        self.total = venta.total
        self.total_con_flete = venta.total_con_flete
        self.abono = venta.abono
        self.saldo = venta.saldo
        self.estado = venta.estado


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="ventas_items")
    
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    precio_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.precio_total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad} en {self.venta.factura}"
