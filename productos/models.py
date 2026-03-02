from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from core.models import AuditModel

class Producto(AuditModel):
    # Identificador único
    id = models.AutoField(primary_key=True)

    # Datos básicos
    nombre = models.CharField(max_length=100, unique=True)  # Ej: Crema, Cuajada, Mantequilla
    descripcion = models.TextField(blank=True, null=True)

    # Imagen (opcional)
    imagen = models.ImageField(
        upload_to="productos/",
        blank=True,
        null=True,
        help_text="Imagen del producto (opcional)"
    )

    # Unidad de medida
    UNIDAD_CHOICES = [
        ('UND', 'Unidad'),
        ('KG', 'Kilogramo'),
        ('LB', 'Libra'),
        ('1/2LB', 'Media Libra'),
        ('CAN', 'Canastilla'),
        ('LTS', 'Litros'),
    ]
    unidad_medida = models.CharField(max_length=10, choices=UNIDAD_CHOICES, default='UND')

    TIPO_CONTROL_CHOICES = [
        ('EXACTO', 'Control por Unidad Exacta (Ej: Doble Crema)'),
        ('PESO', 'Control por Peso con Tolerancia (Ej: Cuajada)'),
    ]
    tipo_control = models.CharField(max_length=15, choices=TIPO_CONTROL_CHOICES, default='EXACTO')
    
    # Tolerancia de pérdida de peso por desuero (Ej: 0.05 para 5%)
    tolerancia_merma = models.DecimalField(max_digits=5, decimal_places=4, default=0.0000, help_text="Tolerancia de merma. Ej: 0.05 para 5%")
    peso_promedio_unidad = models.DecimalField(max_digits=8, decimal_places=3, default=1.000, help_text="Peso base de 1 unidad comercial para conversiones aprox.")

    # Precios
    precio_unitario = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    # Inventario (opcional, si luego quieres manejar stock)
    stock_actual = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    control_inventario = models.BooleanField(default=False, help_text="Si está activo, descuenta stock al vender")

    # Estado
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - {self.precio_unitario} ({self.unidad_medida})"
