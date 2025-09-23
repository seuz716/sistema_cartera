from django.db import models
from clientes.models import Cliente


class Venta(models.Model):
    numero = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="ventas")
    
    embarque = models.CharField(max_length=50)
    dia_embarque = models.PositiveIntegerField()
    fecha = models.DateField()
    factura = models.CharField(max_length=50, unique=True)

    # Datos de transporte
    conductor = models.CharField(max_length=100, blank=True, null=True)
    flete = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Valores financieros globales
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)   # suma de detalles
    descuentos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)      # subtotal - descuentos
    total_con_flete = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Cartera
    abono = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    ESTADO_CHOICES = [
        ('DEBE', 'Debe'),
        ('PAGADA', 'Pagada'),
        ('PARCIAL', 'Pago Parcial'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='DEBE')

    mes = models.CharField(max_length=20)
    dias = models.PositiveIntegerField(default=0)
    promedio = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Factura {self.factura} - {self.cliente.nombre_completo()}"

    def actualizar_totales(self):
        """Recalcula subtotal, total y saldo a partir de los detalles"""
        subtotal = sum(det.precio_total for det in self.detalles.all())
        self.subtotal = subtotal
        self.total = subtotal - self.descuentos
        self.total_con_flete = self.total + self.flete
        self.saldo = self.total_con_flete - self.abono
        self.estado = "PAGADA" if self.saldo <= 0 else ("PARCIAL" if self.abono > 0 else "DEBE")
        self.save()


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")

    # Producto
    producto = models.CharField(max_length=50)  # Crema, Cuajada, Mantequilla, etc.
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unidad_medida = models.CharField(max_length=20, default="UND")  # UND, KG, CANASTILLA
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Extra para productos por peso
    peso_bruto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    peso_neto = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.producto} - {self.cantidad} ({self.venta.factura})"
