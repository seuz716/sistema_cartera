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
        ('compra', 'Compra / Entrada Almacén'),
        ('salida_embarque', 'Salida a tránsito'),
        ('venta', 'Venta'),
        ('devolucion', 'Devolución'),
        ('reposicion', 'Reposición'),
        ('ajuste_merma', 'Merma por desuerado'),
        ('ajuste_diferencia', 'Ajuste diferencia'),
        ('ajuste_positivo', 'Ajuste de inventario (+)'),
        ('retorno_almacen', 'Retorno a almacén (de camión)'),
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

    def save(self, *args, **kwargs):
        from django.db import transaction
        
        with transaction.atomic():
            # =================================================================
            # REGLA ARQUITECTÓNICA: Blindaje del Inventario
            # =================================================================
            # 1. Almacén (stock_actual): 
            #    - Aumenta con: Compras (ajuste_positivo), Retornos de embarque.
            #    - Disminuye con: Salida a tránsito (salida_embarque), Ajustes directos.
            # 2. Tránsito (EmbarqueItem):
            #    - Ya se descuenta del almacén al salir. 
            #    - Las ventas y mermas en tránsito NO descuentan del almacén de nuevo.
            # =================================================================
            
            p = Producto.objects.select_for_update().get(pk=self.producto_id)
            
            # Determinamos el impacto en el Stock de Almacén (Nivel Banco)
            signo_almacen = 0
            
            if self.tipo == 'salida_embarque':
                signo_almacen = -1
            elif self.tipo == 'retorno_almacen': # Nuevo: De camión a bodega
                signo_almacen = 1
            elif self.tipo == 'compra' or self.tipo == 'ajuste_positivo':
                signo_almacen = 1
            elif self.tipo in ['ajuste_merma', 'ajuste_diferencia', 'daño']:
                # Si no tiene embarque, es merma en BODEGA -> Descontar de almacén
                # Si tiene embarque, es merma en TRÁNSITO -> No descuenta de almacén de nuevo
                if not self.embarque:
                    signo_almacen = -1
                else:
                    signo_almacen = 0
            
            # Las 'venta' y 'devolucion' (cliente-camión) nunca tocan Almacén (signo=0)
            
            if signo_almacen != 0:
                delta = 0
                if self.producto.tipo_medida == 'kg':
                    delta = self.cantidad_kg or 0
                elif self.producto.tipo_medida == 'litro':
                    delta = self.cantidad_litros or 0
                else:
                    delta = self.cantidad_unidades or 0
                
                p.stock_actual += (delta * signo_almacen)
                p.save()
            
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} - {self.fecha}"

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']
