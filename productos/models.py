from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from simple_history.models import HistoricalRecords

from core.models import AuditModel

class Producto(AuditModel):
    TIPO_MEDIDA_CHOICES = [
        ('unidad', 'Unidad'),
        ('kg', 'Kilogramo'),
        ('litro', 'Litro'),
    ]

    # Identificador único
    id = models.AutoField(primary_key=True)

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True, help_text="Imagen del producto")
    
    tipo_medida = models.CharField(
        max_length=10, 
        choices=TIPO_MEDIDA_CHOICES, 
        default='unidad'
    )
    controla_peso_variable = models.BooleanField(
        default=False,
        help_text="Si es True, se debe registrar peso (kg) y unidades físicas (ej: Cuajada)."
    )
    
    # Mantenemos estos campos por retrocompatibilidad temporal o para reportes, 
    # pero la lógica principal usará tipo_medida
    unidad_medida_old = models.CharField(max_length=10, choices=[
        ('UND', 'Unidad'), ('KG', 'Kilogramo'), ('LB', 'Libra'), ('1/2LB', 'Media Libra'), ('CAN', 'Canastilla'), ('LTS', 'Litros')
    ], default='UND', db_column='unidad_medida')
    
    tolerancia_merma = models.DecimalField(max_digits=5, decimal_places=4, default=0.0000)
    peso_promedio_unidad = models.DecimalField(max_digits=8, decimal_places=3, default=1.000)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    stock_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0.00"))])
    control_inventario = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    # Auditoría de cambios (Forense)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nombre} - {self.precio_unitario} ({self.tipo_medida})"


class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('salida_embarque', 'Salida a tránsito'),
        ('venta', 'Venta'),
        ('devolucion', 'Devolución'),
        ('reposicion', 'Reposición'),
        ('ajuste_merma', 'Merma por desuerado'),
        ('ajuste_diferencia', 'Ajuste diferencia')
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    embarque = models.ForeignKey('embarques.Embarque', on_delete=models.SET_NULL, null=True, blank=True)
    # En el sistema el modelo Factura es Venta
    factura = models.ForeignKey('ventas.Venta', on_delete=models.SET_NULL, null=True, blank=True)

    tipo = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO_CHOICES)

    cantidad_unidades = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cantidad_kg = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cantidad_litros = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} - {self.fecha}"

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']
