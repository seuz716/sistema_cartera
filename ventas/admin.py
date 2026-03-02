from django.contrib import admin
from .models import Venta, DetalleVenta, ConfiguracionFactura


@admin.register(ConfiguracionFactura)
class ConfiguracionFacturaAdmin(admin.ModelAdmin):
    """Singleton: solo se permite editar el registro existente, no crear nuevos."""
    list_display = ('prefijo', 'numero_inicio')

    def has_add_permission(self, request):
        return not ConfiguracionFactura.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('factura', 'cliente', 'fecha', 'total', 'saldo', 'estado')
    list_filter = ('estado', 'fecha')
    search_fields = ('factura', 'cliente__nombre', 'cliente__numero_identificacion')
    inlines = [DetalleVentaInline]
    readonly_fields = ('id_interno', 'subtotal', 'total', 'total_con_flete', 'abono', 'saldo', 'estado')

@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'unidades_entregadas', 'cantidad_facturada', 'precio_unitario', 'precio_total')
    list_filter = ('producto',)
    search_fields = ('venta__factura', 'producto__nombre')
    readonly_fields = ('precio_total',)
