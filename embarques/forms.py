from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.forms import inlineformset_factory

from .models import (
    Embarque, 
    EmbarqueCarga, 
    GastoEmbarque, 
    Ruta, 
    Vehiculo, 
    Transportador, 
    TipoEmbalaje
)

# ----------------------------
# WIDGETS BOOTSTRAP
# ----------------------------
def bootstrap_input(input_type="text", placeholder=""):
    return forms.TextInput(attrs={"type": input_type, "class": "form-control", "placeholder": placeholder})

def bootstrap_select():
    return forms.Select(attrs={"class": "form-control"})

def bootstrap_number(step="0.01", readonly=False):
    attrs = {"class": "form-control", "step": step}
    if readonly:
        attrs["readonly"] = "readonly"
    return forms.NumberInput(attrs=attrs)

def bootstrap_date():
    return forms.DateInput(attrs={"type": "date", "class": "form-control"})


# ======================
# FORMULARIO EMBARQUE
# ======================
class EmbarqueForm(forms.ModelForm):
    """Formulario para la gestión de embarques (Cabecera)."""

    class Meta:
        model = Embarque
        fields = ["fecha", "ruta", "vehiculo", "transportador", "conductor", "estado"]
        widgets = {
            "fecha": bootstrap_date(),
            "ruta": bootstrap_select(),
            "vehiculo": bootstrap_select(),
            "transportador": bootstrap_select(),
            "conductor": bootstrap_input(placeholder="Nombre del conductor"),
            "estado": bootstrap_select(),
        }


# ======================
# FORMULARIO CARGA (PRODUCTOS QUE SALEN)
# ======================
class EmbarqueCargaForm(forms.ModelForm):
    """
    Formulario para cada línea de producto cargado.
    Aquí es donde el usuario define cuántas unidades salen.
    """
    class Meta:
        model = EmbarqueCarga
        fields = ["producto", "tipo_embalaje", "cantidad_unidades"]
        widgets = {
            "producto": bootstrap_select(),
            "tipo_embalaje": bootstrap_select(),
            "cantidad_unidades": bootstrap_number(step="1"),
        }

    def clean_cantidad_unidades(self):
        cant = self.cleaned_data.get("cantidad_unidades")
        if cant and cant <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero.")
        return cant


EmbarqueCargaFormSet = inlineformset_factory(
    Embarque,
    EmbarqueCarga,
    form=EmbarqueCargaForm,
    extra=3,
    can_delete=True
)


# ======================
# FORMULARIO GASTO OPERATIVO
# ======================
class GastoEmbarqueForm(forms.ModelForm):
    """Formulario para registrar gastos como combustible o peajes."""
    class Meta:
        model = GastoEmbarque
        fields = ["tipo", "descripcion", "monto", "comprobante"]
        widgets = {
            "tipo": bootstrap_select(),
            "descripcion": bootstrap_input(placeholder="Ej: Estación de servicio Texaco"),
            "monto": bootstrap_number(),
            "comprobante": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class TipoEmbalajeForm(forms.ModelForm):
    """Formulario para crear nuevos tipos de embalaje."""
    class Meta:
        model = TipoEmbalaje
        fields = ["nombre", "peso_vacio_kg"]
        widgets = {
            "nombre": bootstrap_input(placeholder="Ej: Canastilla Plástica"),
            "peso_vacio_kg": bootstrap_number(),
        }


class TransportadorForm(forms.ModelForm):
    class Meta:
        model = Transportador
        fields = ["nombre", "documento", "telefono", "tarifa_base_viaje"]
        widgets = {
            "nombre": bootstrap_input(placeholder="Nombre completo"),
            "documento": bootstrap_input(placeholder="NIT/Cédula"),
            "telefono": bootstrap_input(placeholder="Teléfono"),
            "tarifa_base_viaje": bootstrap_number(),
        }


class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = ["nombre", "vehiculo_predeterminado", "ciudades_itinerario"]
        widgets = {
            "nombre": bootstrap_input(placeholder="Ej: Ruta Norte"),
            "vehiculo_predeterminado": bootstrap_select(),
            "ciudades_itinerario": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ["placa", "marca", "modelo", "capacidad_carga_kg"]
        widgets = {
            "placa": bootstrap_input(placeholder="ABC-123"),
            "marca": bootstrap_input(placeholder="Ej: Hino"),
            "modelo": bootstrap_input(placeholder="Ej: 2024"),
            "capacidad_carga_kg": bootstrap_number(),
        }
