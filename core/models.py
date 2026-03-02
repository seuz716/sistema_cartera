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
