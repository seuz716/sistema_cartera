from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
import math
from simple_history.models import HistoricalRecords
from clientes.models import Cliente
from productos.models import Producto
from core.models import AuditModel


# ─────────────────────────────────────────────
# CONFIGURACIÓN DE FACTURAS (singleton)
# ─────────────────────────────────────────────
class ConfiguracionFactura(models.Model):
    """
    Modelo singleton que guarda el prefijo y el número inicial
    de las facturas. Solo debe existir un registro.
    """
    prefijo = models.CharField(
        max_length=10,
        default="FV",
        verbose_name="Prefijo de factura",
        help_text="Ej: FV, FAC, INV"
    )
    numero_inicio = models.PositiveIntegerField(
        default=1,
        verbose_name="Número inicial",
        help_text="El consecutivo empezará desde este número."
    )

    class Meta:
        verbose_name = "Configuración de Facturas"
        verbose_name_plural = "Configuración de Facturas"

    def __str__(self):
        return f"Configuración: prefijo={self.prefijo}, inicio={self.numero_inicio}"

    @classmethod
    def get_config(cls):
        """Devuelve la configuración actual o la crea con valores por defecto."""
        config, _ = cls.objects.get_or_create(pk=1)
        return config


# ─────────────────────────────────────────────
# GENERADOR DE CONSECUTIVO
# ─────────────────────────────────────────────
def generar_consecutivo():
    """
    Genera el siguiente número de factura basado en la configuración
    y el último registro existente. Thread-safe via UNIQUE en DB.
    """
    config = ConfiguracionFactura.get_config()
    prefijo = config.prefijo
    inicio = config.numero_inicio

    last = (
        Venta.objects
        .filter(factura__startswith=prefijo)
        .order_by('-id_interno')
        .first()
    )

    if last:
        try:
            num_actual = int(last.factura.replace(prefijo, "", 1))
            siguiente = num_actual + 1
        except (ValueError, AttributeError):
            siguiente = inicio
    else:
        siguiente = inicio

    return f"{prefijo}{siguiente}"



class Venta(AuditModel):
    # Consecutivo interno sistema
    id_interno = models.AutoField(primary_key=True)
    # Número de factura visible (manual o auto)
    factura = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="N° Factura",
        help_text="Se genera automáticamente. No editar."
    )
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="ventas")
    
    fecha = models.DateField()
    embarque = models.ForeignKey(
        'embarques.Embarque',
        on_delete=models.PROTECT,
        related_name="ventas",
        null=False,
        blank=False,
        verbose_name="Embarque / Ruta"
    )
    conductor = models.CharField(max_length=150, blank=True, null=True)
    placa = models.CharField(max_length=20, blank=True, null=True)
    
    # Datos de entrega y conciliación física
    total_embalajes_entregados = models.PositiveIntegerField(default=0, help_text="Canastillas físicamente entregadas")
    total_embalajes_devueltos = models.PositiveIntegerField(default=0, help_text="Canastillas que regresaron (devolución/cambio)")

    # Datos de transporte
    flete = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Valores financieros globales
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuentos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_con_flete = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Automatización de Embalajes (Nivel Banco)
    total_embalajes_automatico = models.BooleanField(
        default=True, 
        help_text="Si está activo, el sistema estima las canastillas según la configuración del producto"
    )

    # Cartera
    abono = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Estado y Auditoría
    confirmado = models.BooleanField(default=False, help_text="Venta confirmada por el cargador/controlador")

    ESTADO_CHOICES = [
        ('DEBE', 'Pendiente (Crédito)'),
        ('PAGADA', 'Pagada Totalmente'),
        ('PARCIAL', 'Abonada / Parcial'),
        ('ANULADA', 'Anulada'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='DEBE')

    notas = models.TextField(blank=True, null=True)

    # Auditoría Forense
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['estado']),
            models.Index(fields=['factura']),
        ]
        ordering = ['-fecha', '-id_interno']

    def clean(self):
        if self.descuentos < 0:
            raise ValidationError({'descuentos': "Los descuentos no pueden ser negativos."})
        if self.flete < 0:
            raise ValidationError({'flete': "El flete no puede ser negativo."})
        if self.abono < 0:
            raise ValidationError({'abono': "El abono no puede ser negativo."})

    def __str__(self) -> str:
        return f"Factura {self.factura} - {self.cliente}"

    def save(self, *args, **kwargs):
        if not self.factura:
            self.factura = generar_consecutivo()
        super().save(*args, **kwargs)

    def actualizar_totales(self) -> None:
        """
        Recalcula subtotal, total, abono y saldo a partir de los detalles y pagos
        relacionados, actualizando el estado de la factura (DEBE, PARCIAL, PAGADA).
        Usa select_for_update para prevenir race conditions.
        """
        # 1. Bloqueo de fila para evitar que otro proceso pise el saldo
        # Refrescamos desde la DB para tener valores exactos
        venta = Venta.objects.select_for_update().get(pk=self.pk)

        # 2. Totales de productos (usando agregación en DB para mayor precisión y rendimiento)
        subtotal = venta.detalles.aggregate(total=models.Sum('precio_total'))['total'] or Decimal('0.00')
        
        venta.subtotal = subtotal
        # Descuentos restan del subtotal
        venta.total = subtotal - venta.descuentos
        # Flete RESTA al total final (gasto/comisión asumido de la venta o descuento logístico)
        venta.total_con_flete = venta.total - venta.flete

        # 3. Recalcular Abonos (usando agregación)
        venta.abono = venta.pagos.aggregate(total=models.Sum('monto'))['total'] or Decimal('0.00')

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
            
        # 5. Sincronizar Embalajes (Nivel Banco: Cuadre físico vs Pago Transportador)
        # PROTECCIÓN HISTÓRICA: Solo recalculamos si el embarque permite cambios (Programado/Cargando)
        # o si no tiene embarque aún. Si ya está EN_RUTA o superior, el dato es INMUTABLE.
        # EXCEPCIÓN: Si el total actual es 0, permitimos la primera sincronización.
        puedo_recalcular = True
        if venta.embarque and venta.embarque.estado not in ['PROGRAMADO', 'CARGANDO']:
             if venta.total_embalajes_entregados > 0:
                puedo_recalcular = False

        if venta.total_embalajes_automatico and puedo_recalcular:
            total_emb = Decimal('0')
            for det in venta.detalles.all():
                det.calcular_unidades_embalaje() 
                total_emb += Decimal(str(det.embalajes_entregados))
            venta.total_embalajes_entregados = int(total_emb)

        # 6. Guardar cambios
        venta.save()
        
        # 6. Sincronizar el objeto actual en memoria
        self.refresh_from_db()

    @property
    def total_items(self):
        """Total solo de los items sin impuestos ni fletes."""
        return self.subtotal

    @property
    def saldo_pendiente(self):
        """Alias dinámico para saldo por claridad en templates."""
        return self.saldo


class DetalleVenta(AuditModel):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="ventas_items")
    embarque_item = models.ForeignKey(
        'embarques.EmbarqueItem', 
        on_delete=models.PROTECT, 
        related_name="detalles_venta",
        null=True, # Permitir nulo para ventas sin embarque si el sistema lo permite, pero la regla dice que debe seleccionar embarque
        blank=True
    )
    
    # Estos campos reemplazan unidades_entregadas y cantidad_facturada en la nueva lógica
    cantidad_unidades = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cantidad_kg = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cantidad_litros = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Mantenemos por compatibilidad y para reportes rápidos (se sincronizarán)
    unidades_entregadas = models.PositiveIntegerField(default=1)
    cantidad_facturada = models.DecimalField(max_digits=12, decimal_places=2)
    
    unidades_devueltas = models.PositiveIntegerField(default=0)
    cantidad_devuelta_facturada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    precio_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    # Relación con el transporte (Nivel Banco)
    embalajes_entregados = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Canastillas calculadas para este item"
    )

    @property
    def cantidad(self):
        """Devuelve la cantidad en la unidad de medida principal (UND, KG o LTS)."""
        if self.producto.tipo_medida == 'kg':
             return self.cantidad_kg or 0
        elif self.producto.tipo_medida == 'litro':
             return self.cantidad_litros or 0
        return self.cantidad_unidades or 0

    history = HistoricalRecords()

    def calcular_unidades_embalaje(self):
        """
        Calcula cuántas canastillas (o unidad logística) ocupa este detalle.
        Si el producto tiene una CapacidadEmbalaje configurada, usa esa base.
        """
        from embarques.models import CapacidadEmbalaje
        import math
        
        # Intentamos obtener la capacidad estándar (asumiendo 'Canastilla' como base si hay varias)
        # O la primera que encuentre para el producto.
        capacidad = CapacidadEmbalaje.objects.filter(producto=self.producto).first()
        
        if capacidad and capacidad.unidades_por_paquete > 0:
            # Decidimos qué base usar para el cálculo
            base_calculo = Decimal('0')
            if capacidad.metodo_calculo == 'UNIDADES':
                # Base: unidades físicas (bloques, bolsas)
                base_calculo = Decimal(str(self.unidades_entregadas))
            else:
                # Base: cantidad comercial (Kg, Litros)
                base_calculo = self.cantidad_facturada

            # Cálculo: base / capacidad = embalajes (redondeo hacia arriba)
            self.embalajes_entregados = Decimal(str(math.ceil(base_calculo / capacidad.unidades_por_paquete)))
        else:
            # Si no hay configuración, mantenemos lo que hay (o 0)
            pass

    def save(self, *args, **kwargs):
        from django.db import transaction
        from django.core.exceptions import ValidationError
        from productos.models import MovimientoInventario

        # 1. Sincronización de campos nuevos -> viejos
        if self.cantidad_unidades is not None:
             self.unidades_entregadas = int(self.cantidad_unidades)
        
        if self.producto.tipo_medida == 'kg':
            if self.cantidad_kg is not None:
                self.cantidad_facturada = self.cantidad_kg
        elif self.producto.tipo_medida == 'litro':
            if self.cantidad_litros is not None:
                self.cantidad_facturada = self.cantidad_litros
        else:
            if self.cantidad_unidades is not None:
                self.cantidad_facturada = self.cantidad_unidades

        # 2. Cálculos base
        self.precio_total = (self.cantidad_facturada or 0) * (self.precio_unitario or 0)

        # 2. Lógica de Inventario (Solo si la venta tiene un embarque)
        if self.venta.embarque and not self.embarque_item:
            from embarques.models import EmbarqueItem
            try:
                self.embarque_item = EmbarqueItem.objects.get(
                    embarque=self.venta.embarque, 
                    producto=self.producto
                )
            except EmbarqueItem.DoesNotExist:
                # Si el producto no está en el embarque, no podemos descontar inventario.
                # Dependiendo de la política, esto podría ser un error o permitirse.
                # Según el usuario, "entra al inventario en transito y... debe ir restando".
                # Así que debería estar en el embarque.
                pass

        if self.embarque_item:
            with transaction.atomic():
                # Bloquear el embarque_item para evitar concurrencia
                from embarques.models import EmbarqueItem
                emb_item = EmbarqueItem.objects.select_for_update().get(pk=self.embarque_item.pk)
                
                # Valores a descontar
                req_unidades = self.cantidad_unidades or 0
                req_kg = self.cantidad_kg or 0
                req_litros = self.cantidad_litros or 0

                # Si es una edición, sumar lo anterior al disponible antes de validar
                if self.pk:
                    old_obj = DetalleVenta.objects.get(pk=self.pk)
                    emb_item.cantidad_disponible_unidades += old_obj.cantidad_unidades or 0
                    emb_item.cantidad_disponible_kg += old_obj.cantidad_kg or 0
                    emb_item.cantidad_disponible_litros += old_obj.cantidad_litros or 0
                
                # Validar disponibilidad
                if self.producto.tipo_medida == 'kg':
                    if req_kg > emb_item.cantidad_disponible_kg:
                        raise ValidationError(f"Stock insuficiente en embarque para {self.producto.nombre}. Disponible: {emb_item.cantidad_disponible_kg} kg")
                elif self.producto.tipo_medida == 'litro':
                    if req_litros > emb_item.cantidad_disponible_litros:
                        raise ValidationError(f"Stock insuficiente en embarque para {self.producto.nombre}. Disponible: {emb_item.cantidad_disponible_litros} lts")
                else:
                    if req_unidades > emb_item.cantidad_disponible_unidades:
                        raise ValidationError(f"Stock insuficiente en embarque para {self.producto.nombre}. Disponible: {emb_item.cantidad_disponible_unidades} und")
                
                # Descontar
                emb_item.cantidad_disponible_unidades -= req_unidades
                emb_item.cantidad_disponible_kg -= req_kg
                emb_item.cantidad_disponible_litros -= req_litros
                emb_item.save()

                super().save(*args, **kwargs)

                # Registrar movimiento de inventario (Audit)
                # Primero, si es edición, podemos anular el movimiento anterior o crear un ajuste.
                # Para simplificar, crearemos un movimiento por cada guardado que reste al inventario.
                # En un sistema real, querríamos rastrear el cambio neto.
                MovimientoInventario.objects.create(
                    producto=self.producto,
                    embarque=self.venta.embarque,
                    factura=self.venta,
                    tipo='venta',
                    cantidad_unidades=-req_unidades,
                    cantidad_kg=-req_kg,
                    cantidad_litros=-req_litros,
                    descripcion=f"Venta Factura {self.venta.factura}"
                )
        else:
            super().save(*args, **kwargs)

        # 3. Recalcular embalajes si es necesario
        if self.venta.total_embalajes_automatico:
            self.calcular_unidades_embalaje()
            super().save(update_fields=['embalajes_entregados'])

    def delete(self, *args, **kwargs):
        from django.db import transaction
        from productos.models import MovimientoInventario
        
        if self.embarque_item:
            with transaction.atomic():
                from embarques.models import EmbarqueItem
                emb_item = EmbarqueItem.objects.select_for_update().get(pk=self.embarque_item.pk)
                
                # Devolver al disponible
                emb_item.cantidad_disponible_unidades += self.cantidad_unidades or 0
                emb_item.cantidad_disponible_kg += self.cantidad_kg or 0
                emb_item.cantidad_disponible_litros += self.cantidad_litros or 0
                emb_item.save()

                # Registrar movimiento de reversión
                MovimientoInventario.objects.create(
                    producto=self.producto,
                    embarque=self.venta.embarque,
                    factura=self.venta,
                    tipo='ajuste_reversion',
                    cantidad_unidades=self.cantidad_unidades or 0,
                    cantidad_kg=self.cantidad_kg or 0,
                    cantidad_litros=self.cantidad_litros or 0,
                    descripcion=f"Reversión Venta Factura {self.venta.factura} (Item Eliminado)"
                )
        
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad} en {self.venta.factura}"
