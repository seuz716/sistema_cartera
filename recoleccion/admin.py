# recoleccion/admin.py
from django.contrib import admin
from .models import Ruta, Recoleccion


@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'zona')
    search_fields = ('nombre', 'zona')
    ordering = ('nombre',)


@admin.register(Recoleccion)
class RecoleccionAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'fecha', 'litros', 'quincena')
    list_filter = ('fecha',)
    search_fields = ('proveedor__nombre',)
    ordering = ('-fecha',)

    # Opcional: mostrar la ruta relacionada (si Proveedor tiene campo 'ruta')
    def ruta(self, obj):
        return getattr(obj.proveedor.ruta, "nombre", "-")
    ruta.short_description = "Ruta"
