from django.contrib import admin
from .models import Producto
from .forms import ProductoForm


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoForm

    # columnas que se muestran en el listado
    list_display = (
        "nombre",
        "unidad_medida",
        "precio_unitario",
        "stock_actual",
        "control_inventario",
        "activo",
        "fecha_creacion",
        "fecha_actualizacion",
    )

    # enlaces clicables en el listado
    list_display_links = ("nombre",)

    # búsqueda por nombre y descripción
    search_fields = ("nombre", "descripcion")

    # filtros laterales
    list_filter = ("unidad_medida", "activo", "control_inventario")

    # orden por defecto
    ordering = ("nombre",)

    # campos de solo lectura
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")

    # organización de los campos en el formulario del admin
    fieldsets = (
        ("Información básica", {
            "fields": ("nombre", "descripcion", "imagen", "unidad_medida", "precio_unitario"),
        }),
        ("Inventario", {
            "fields": ("stock_actual", "control_inventario"),
        }),
        ("Estado", {
            "fields": ("activo",),
        }),
        ("Auditoría", {
            "fields": ("fecha_creacion", "fecha_actualizacion"),
            "classes": ("collapse",),
        }),
    )

    # ✅ NUEVO: miniatura de la imagen en el listado
    def imagen_preview(self, obj):
        if obj.imagen:
            return f'<img src="{obj.imagen.url}" width="50" height="50" style="object-fit:cover;border-radius:4px;" />'
        return "—"
    imagen_preview.allow_tags = True
    imagen_preview.short_description = "Imagen"

    # Agregar la imagen al listado (al inicio)
    list_display = ("imagen_preview",) + list_display

    # ✅ NUEVO: edición rápida desde la lista
    list_editable = ("precio_unitario", "stock_actual", "control_inventario", "activo")
