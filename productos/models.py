from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from simple_history.models import HistoricalRecords

from core.models import AuditModel

class Producto(AuditModel):
    # Identificador único
    id = models.AutoField(primary_key=True)

    # ... (rest of the fields) ...
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True, help_text="Imagen del producto")
    unidad_medida = models.CharField(max_length=10, choices=[
        ('UND', 'Unidad'), ('KG', 'Kilogramo'), ('LB', 'Libra'), ('1/2LB', 'Media Libra'), ('CAN', 'Canastilla'), ('LTS', 'Litros')
    ], default='UND')
    tipo_control = models.CharField(max_length=15, choices=[
        ('EXACTO', 'Control por Unidad Exacta'), ('PESO', 'Control por Peso con Tolerancia')
    ], default='EXACTO')
    tolerancia_merma = models.DecimalField(max_digits=5, decimal_places=4, default=0.0000)
    peso_promedio_unidad = models.DecimalField(max_digits=8, decimal_places=3, default=1.000)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    stock_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0.00"))])
    control_inventario = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    # Auditoría de cambios (Forense)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nombre} - {self.precio_unitario} ({self.unidad_medida})"
