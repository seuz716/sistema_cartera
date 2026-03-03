from django.contrib import admin
from .models import LogsActividad

@admin.register(LogsActividad)
class LogsActividadAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'tipo', 'usuario', 'descripcion')
    list_filter = ('tipo', 'usuario')
    search_fields = ('descripcion', 'referencia_id')
    readonly_fields = ('fecha', 'usuario', 'tipo', 'descripcion', 'referencia_id', 'metadata')
