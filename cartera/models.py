from django.db import models
from django.core.exceptions import ValidationError
from ventas.models import Venta


class Pago(models.Model):
    METODO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('CHEQUE', 'Cheque'),
        ('TERCERO', 'Pago por Tercero'),
        ('OTRO', 'Otro'),
    ]

    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="pagos")
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_CHOICES, default='EFECTIVO')
    
    # Si el pago lo hace alguien más (Pago por Tercero)
    pagado_por = models.CharField(max_length=150, blank=True, null=True, help_text="Nombre del tercero si aplica")
    
    referencia = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° Comprobante / Referencia")
    notas = models.TextField(blank=True, null=True)
    
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Valida que el pago no sea negativo y no exceda el saldo de la venta."""
        if self.monto <= 0:
            raise ValidationError("El monto del pago debe ser mayor a 0.")
        
        # Si es un pago nuevo o modificado, verificamos el saldo pendiente
        # Ignoramos el propio monto actual si estamos editando
        saldo_actual = self.venta.total_con_flete - sum(p.monto for p in self.venta.pagos.exclude(pk=self.pk))
        
        if self.monto > saldo_actual:
            raise ValidationError(f"El monto del pago (${self.monto}) excede el saldo pendiente (${saldo_actual}).")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pago {self.id} - {self.monto} (Fact: {self.venta.factura})"
