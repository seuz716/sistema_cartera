import hashlib
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from clientes.models import Cliente
from ventas.models import Venta
from core.models import AuditModel

class ReciboCaja(AuditModel):
    """
    Representa un ingreso de dinero global de un cliente.
    Este recibo puede cubrir múltiples facturas (Cascading Payments).
    """
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="recibos_caja")
    fecha = models.DateField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=[
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('CHEQUE', 'Cheque'),
        ('TERCERO', 'Pago por Tercero'),
        ('OTRO', 'Otro'),
    ], default='EFECTIVO')
    referencia = models.CharField(max_length=100, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Recibo de Caja"
        verbose_name_plural = "Recibos de Caja"
        ordering = ['-fecha', '-fecha_creacion']

    def __str__(self):
        return f"RC-{self.id} | {self.cliente.nombre} | ${self.monto_total}"

    def registrar_y_distribuir(self, usuario):
        """
        Lógica de Cascada Financiera (Forensic Audit):
        Toma el monto total y lo aplica a facturas pendientes (FIFO).
        """
        from django.db import transaction
        from core.models import LogsActividad
        from decimal import Decimal

        with transaction.atomic():
            self.usuario_registro = usuario
            self.save()

            monto_restante = self.monto_total
            # Obtener facturas pendientes ordenadas por ID interno (FIFO aproximado por registro)
            ventas_pendientes = Venta.objects.filter(
                cliente=self.cliente, 
                saldo__gt=0
            ).exclude(estado='ANULADA').order_by('id_interno')

            aplicaciones = []
            for venta in ventas_pendientes:
                if monto_restante <= 0:
                    break
                
                cuanto_debe = venta.saldo
                cuanto_pagar = min(cuanto_debe, monto_restante)
                
                # Crear el pago individual (Aplicación)
                Pago.objects.create(
                    recibo=self,
                    venta=venta,
                    cliente=self.cliente,
                    fecha=self.fecha,
                    monto=cuanto_pagar,
                    metodo_pago=self.metodo_pago,
                    referencia=self.referencia,
                    usuario_registro=usuario
                )
                
                monto_restante -= cuanto_pagar
                aplicaciones.append(f"Fact {venta.factura}: ${cuanto_pagar}")
                
            # Log Forense
            desc = f"Recibo RC-{self.id} de ${self.monto_total} aplicado a: " + ", ".join(aplicaciones)
            if monto_restante > 0:
                desc += f". Excedente favor: ${monto_restante}."
            
            LogsActividad.objects.create(
                usuario=usuario,
                tipo='FINANCIERO',
                descripcion=desc,
                referencia_id=f"RECIBO_{self.id}",
                metadata={
                    'recibo_id': self.id,
                    'monto': str(self.monto_total),
                    'excedente': str(monto_restante),
                    'aplicaciones': aplicaciones
                }
            )
            return monto_restante

class Pago(AuditModel):
    METODO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('CHEQUE', 'Cheque'),
        ('TERCERO', 'Pago por Tercero'),
        ('OTRO', 'Otro'),
    ]

    recibo = models.ForeignKey(ReciboCaja, on_delete=models.CASCADE, related_name="aplicaciones", null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="pagos", null=True, blank=True)
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="pagos")
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_CHOICES, default='EFECTIVO')
    
    # Si el pago lo hace alguien más (Pago por Tercero)
    pagado_por = models.CharField(max_length=150, blank=True, null=True, help_text="Nombre del tercero si aplica")
    
    referencia = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° Comprobante / Referencia")
    notas = models.TextField(blank=True, null=True)
    
    # Nivel Banco
    hash_integridad = models.CharField(max_length=64, editable=False, blank=True)
    
    # Auditoría Forense
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha', '-fecha_creacion']
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'fecha', 'referencia'],
                name='unique_pago_cliente_fecha_referencia',
                condition=models.Q(referencia__isnull=False)
            )
        ]

    def clean(self):
        """
        Valida que el pago sea positivo, no exceda el saldo y 
        no sea un duplicado para el cliente en el mismo día.
        """
        # 0. Nivel Banco: No permitir edición de pagos ya guardados (Inmutabilidad)
        if self.pk:
            raise ValidationError("Los registros de pago son inmutables. No se permite editar un pago confirmado.")

        if self.monto <= 0:
            raise ValidationError("El monto del pago debe ser mayor a 0.")
        
        # Sincronizar cliente desde la venta si no está puesto
        if not self.cliente and self.venta:
            self.cliente = self.venta.cliente

        # Normalización de referencia (Bank standard)
        if self.referencia:
            self.referencia = self.referencia.strip().upper()

        # 1. Validar que no exceda el saldo pendiente (considerando si es edición)
        from decimal import Decimal
        pagos_previos = self.venta.pagos.exclude(pk=self.pk).aggregate(
            total=models.Sum('monto'))['total'] or Decimal('0.00')
        
        saldo_actual = self.venta.total_con_flete - pagos_previos
        
        if self.monto > saldo_actual:
            raise ValidationError(
                f"El monto del pago (${self.monto}) excede el saldo pendiente (${saldo_actual})."
            )

        # 2. Validar duplicados por CLIENTE, FECHA y REFERENCIA (Nivel Senior)
        if self.referencia:
            existe_duplicado = Pago.objects.filter(
                cliente=self.cliente,
                fecha=self.fecha,
                referencia=self.referencia
            ).exclude(pk=self.pk).exists()

            if existe_duplicado:
                raise ValidationError(
                    "Ya existe un pago con esta referencia para este cliente en esta fecha."
                )

    def save(self, *args, **kwargs):
        # Asegurar que el cliente siempre coincida con la venta antes de validar/guardar
        if self.venta:
            self.cliente = self.venta.cliente
        
        # Normalización antes de full_clean
        if self.referencia:
            self.referencia = self.referencia.strip().upper()

        self.full_clean()
        
        # Nivel Banco: Generar Hash de Integridad antes de guardar
        if not self.hash_integridad:
            string_para_hash = f"{self.venta_id}|{self.cliente_id}|{self.fecha}|{self.monto}|{self.referencia}|{self.usuario_registro_id}"
            self.hash_integridad = hashlib.sha256(string_para_hash.encode()).hexdigest()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pago {self.id} - {self.monto} (Fact: {self.venta.factura})"
