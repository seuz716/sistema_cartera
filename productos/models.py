from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Producto(models.Model):
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

    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} - {self.precio_unitario} ({self.unidad_medida})"
