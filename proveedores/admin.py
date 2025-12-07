# proveedores/admin.py
from django.contrib import admin
from .models import Proveedor

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'identificacion', 'telefono', 'email')
    search_fields = ('nombre', 'identificacion')
    ordering = ('nombre',)
