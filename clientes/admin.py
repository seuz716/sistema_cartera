from django.contrib import admin
from .models import Cliente
from .forms import ClienteForm


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    form = ClienteForm

    readonly_fields = (
        'saldo',
        'fecha_creacion',
        'fecha_actualizacion',
    )

    fieldsets = (
        ("Información Personal", {
            "fields": (
                ("numero_identificacion", "tipo_persona"),
                ("nombre", "apellido"),
                "email", "telefono",
                "direccion", "ciudad",
            )
        }),
        ("Condiciones de Pago", {
            "fields": (
                "forma_pago",
                "dias_credito",
                "saldo",
            )
        }),
        ("Estado", {
            "fields": ("activo",),
        }),
        ("Trazabilidad", {
            "fields": ("fecha_creacion", "fecha_actualizacion"),
        }),
    )
