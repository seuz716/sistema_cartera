from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.forms import inlineformset_factory

from .models import (
    Embarque, 
    EmbarqueItem, 
    GastoEmbarque, 
    NovedadEmbarque,
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

def bootstrap_number(step="0.01", readonly=False, placeholder=""):
    attrs = {"class": "form-control", "step": step, "placeholder": placeholder}
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
        model = EmbarqueItem
        fields = ["producto", "cantidad_unidades", "cantidad_kg", "cantidad_litros", "tipo_embalaje"]
        widgets = {
            "producto": bootstrap_select(),
            "cantidad_unidades": bootstrap_number(step="1", placeholder="Und"),
            "cantidad_kg": bootstrap_number(step="0.01", placeholder="Kg"),
            "cantidad_litros": bootstrap_number(step="0.01", placeholder="Lts"),
            "tipo_embalaje": bootstrap_select(),
        }

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get("producto")
        cant_und = cleaned_data.get("cantidad_unidades")
        cant_kg = cleaned_data.get("cantidad_kg")
        cant_lts = cleaned_data.get("cantidad_litros")

        if not producto:
            return cleaned_data

        if producto.tipo_medida == 'kg' and not cant_kg:
            raise ValidationError("Debe especificar los kilogramos (kg) para este producto.")
        if producto.tipo_medida == 'litro' and not cant_lts:
            raise ValidationError("Debe especificar los litros (lts) para este producto.")
        if producto.tipo_medida == 'unidad' and not cant_und:
            raise ValidationError("Debe especificar las unidades (und) para este producto.")
        
        return cleaned_data


EmbarqueCargaFormSet = inlineformset_factory(
    Embarque,
    EmbarqueItem,
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
class NovedadEmbarqueForm(forms.ModelForm):
    cantidad = forms.DecimalField(
        label="Cantidad (Und o Kg)", 
        widget=bootstrap_number(),
        help_text="Ingrese la cantidad en la unidad de medida del producto."
    )

    class Meta:
        model = NovedadEmbarque
        fields = ["producto", "tipo", "cantidad", "descripcion"]
        widgets = {
            "producto": bootstrap_select(),
            "tipo": bootstrap_select(),
            "descripcion": bootstrap_input(placeholder="Ej: Se rompió en el descargue"),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        cantidad = self.cleaned_data.get("cantidad")
        if instance.producto.tipo_medida == 'kg':
            instance.cantidad_kg = cantidad
            instance.cantidad_unidades = 0
            instance.cantidad_litros = 0
        elif instance.producto.tipo_medida == 'litro':
            instance.cantidad_litros = cantidad
            instance.cantidad_unidades = 0
            instance.cantidad_kg = 0
        else:
            instance.cantidad_unidades = cantidad
            instance.cantidad_kg = 0
            instance.cantidad_litros = 0
        
        if commit:
            instance.save()
        return instance
