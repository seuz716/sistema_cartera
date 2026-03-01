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
        Recalcula subtotal, total y saldo a partir de los detalles relacionados
        y actualiza el estado de la factura (DEBE, PARCIAL, PAGADA).
        """
        detalles = self.detalles.all()
        subtotal = sum(det.precio_total for det in detalles)
        self.subtotal = subtotal
        self.total = subtotal - self.descuentos
        self.total_con_flete = self.total + self.flete
        # El saldo se calcula restando los abonos registrados
        self.saldo = self.total_con_flete - self.abono
        
        if self.saldo <= 0:
            self.estado = "PAGADA"
        elif self.abono > 0:
            self.estado = "PARCIAL"
        else:
            self.estado = "DEBE"
            
        self.save()


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
