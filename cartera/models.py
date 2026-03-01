from django.db import models
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

    def __str__(self):
        return f"Pago {self.id} - {self.monto} (Fact: {self.venta.factura})"
