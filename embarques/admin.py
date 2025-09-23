from django.contrib import admin
from .models import Embarque, CostoEmbarque, TipoCosto

# -----------------------------
# Inline de costos
# -----------------------------
class CostoEmbarqueInline(admin.TabularInline):
    model = CostoEmbarque
    extra = 1
    readonly_fields = ('monto', 'creado_en', 'actualizado_en')


# -----------------------------
# Admin de Embarque
# -----------------------------
@admin.register(Embarque)
class EmbarqueAdmin(admin.ModelAdmin):
    list_display = ('numero', 'fecha', 'conductor', 'vehiculo', 'mostrar_costo_total')
    search_fields = ('numero', 'conductor', 'vehiculo')
    inlines = [CostoEmbarqueInline]

    def mostrar_costo_total(self, obj):
        return f"${obj.costo_total:,.2f}"
    mostrar_costo_total.short_description = "Costo Total"


# -----------------------------
# Admin de CostoEmbarque
# -----------------------------
@admin.register(CostoEmbarque)
class CostoEmbarqueAdmin(admin.ModelAdmin):
    list_display = ('embarque', 'tipo', 'monto', 'fecha')
    list_filter = ('tipo', 'fecha')
    search_fields = ('descripcion', 'tipo__nombre')
    autocomplete_fields = ('tipo',)


# -----------------------------
# Admin de TipoCosto
# -----------------------------
@admin.register(TipoCosto)
class TipoCostoAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)
