from django.db import models
from django.conf import settings

class AuditModel(models.Model):
    """
    Modelo abstracto para trazabilidad (Audit Trail).
    Registra automáticamente fechas de creación y modificación.
    """
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Última Modificación")
    
    # Usuario que realizó la acción (requiere asignación manual en la vista o middleware)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="%(class)s_registros"
    )

    class Meta:
        abstract = True

class LogsActividad(models.Model):
    """
    Registro de eventos críticos del sistema (Auditoría Forense).
    Especialmente para trazabilidad de pagos, cambios de precios y saldos.
    """
    TIPO_CHOICES = [
        ('FINANCIERO', 'Evento Financiero (Pago/Saldo)'),
        ('LOGISTICO', 'Evento Logístico (Carga/Entrega)'),
        ('SISTEMA', 'Cambio de Configuración / Precios'),
        ('ALERTA', 'Alerta de Seguridad o Descuadre'),
    ]
    
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='FINANCIERO')
    descripcion = models.TextField()
    
    # Referencias genéricas para trazabilidad (pueden ser IDs de facturas, clientes, etc.)
    referencia_id = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Datos técnicos del evento (ej: payload antes/después)")

    class Meta:
        verbose_name = "Log de Actividad"
        verbose_name_plural = "Logs de Actividad"
        ordering = ['-fecha']

    def __str__(self):
        return f"[{self.tipo}] {self.fecha.strftime('%Y-%m-%d %H:%M')} - {self.descripcion[:50]}"
