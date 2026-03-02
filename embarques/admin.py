from django.contrib import admin
from .models import (
    Vehiculo, Transportador, Ruta, TipoEmbalaje, 
    CapacidadEmbalaje, TarifaTransporte, Embarque, 
    EmbarqueCarga, GastoEmbarque
)

class EmbarqueCargaInline(admin.TabularInline):
    model = EmbarqueCarga
    extra = 1

class GastoEmbarqueInline(admin.TabularInline):
    model = GastoEmbarque
    extra = 1

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'marca', 'modelo', 'activo')
    list_editable = ('activo',)

@admin.register(Transportador)
class TransportadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'documento', 'telefono', 'activo')
    list_editable = ('activo',)

@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_editable = ('activo',)

@admin.register(TipoEmbalaje)
class TipoEmbalajeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'peso_vacio_kg')

@admin.register(CapacidadEmbalaje)
class CapacidadEmbalajeAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo_embalaje', 'unidades_por_paquete')
    list_filter = ('tipo_embalaje', 'producto')

@admin.register(TarifaTransporte)
class TarifaTransporteAdmin(admin.ModelAdmin):
    list_display = ('transportador', 'ruta', 'ciudad', 'precio_por_embalaje')
    list_filter = ('transportador', 'ruta')

@admin.register(Embarque)
class EmbarqueAdmin(admin.ModelAdmin):
    list_display = (
        'numero', 'fecha', 'ruta', 'vehiculo', 
        'transportador', 'estado', 'utilidad_neta'
    )
    list_filter = ('estado', 'fecha', 'ruta')
    search_fields = ('numero',)
    inlines = [EmbarqueCargaInline, GastoEmbarqueInline]
    readonly_fields = ('numero', 'peso_total_kg', 'ingresos_ventas', 'gastos_operativos', 'pago_transportador', 'utilidad_neta', 'fecha_creacion', 'fecha_modificacion')
    
    fieldsets = (
        ('Información General', {
            'fields': ('numero', 'fecha', 'ruta', 'vehiculo', 'transportador', 'estado', 'usuario_registro')
        }),
        ('Conciliación Física', {
            'fields': ('total_embalajes_enviados', 'total_embalajes_entregados', 'total_embalajes_devueltos')
        }),
        ('Resultados Financieros', {
            'fields': ('ingresos_ventas', 'gastos_operativos', 'pago_transportador', 'utilidad_neta')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
        }),
    )
