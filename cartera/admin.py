from django.contrib import admin
from .models import Pago

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'venta', 'monto', 'fecha', 'metodo_pago')
    list_filter = ('metodo_pago', 'fecha')
    search_fields = ('venta__factura', 'venta__cliente__nombre', 'referencia')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
