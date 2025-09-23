from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import Embarque, CostoEmbarque, TipoCosto


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
    """
    Formulario para crear/editar embarques.
    Normaliza entradas de texto (conductor, vehículo, placa).
    """

    class Meta:
        model = Embarque
        fields = ["fecha", "conductor", "vehiculo", "placa"]
        widgets = {
            "fecha": bootstrap_date(),
            "conductor": bootstrap_input(placeholder="Nombre del conductor"),
            "vehiculo": bootstrap_input(placeholder="Ej: Camión 3.5T"),
            "placa": bootstrap_input(placeholder="ABC123"),
        }

    def clean_conductor(self):
        conductor = self.cleaned_data.get("conductor", "").strip().title()
        if not conductor:
            raise ValidationError("El nombre del conductor es obligatorio.")
        return conductor

    def clean_vehiculo(self):
        vehiculo = self.cleaned_data.get("vehiculo", "")
        return vehiculo.strip().title() if vehiculo else vehiculo

    def clean_placa(self):
        placa = self.cleaned_data.get("placa", "")
        return placa.strip().upper() if placa else placa


# ======================
# FORMULARIO COSTO EMBARQUE
# ======================
class CostoEmbarqueForm(forms.ModelForm):
    """
    Formulario profesional para registrar costos de embarque.
    Calcula monto automáticamente y asegura coherencia entre cantidad, precio y unidad.
    """

    class Meta:
        model = CostoEmbarque
        fields = [
            "embarque",
            "tipo",
            "descripcion",
            "cantidad",
            "unidad",
            "precio_unitario",
            "monto",
            "fecha",
            "recibo",
        ]
        widgets = {
            "embarque": forms.HiddenInput(),  # Se asigna desde la vista
            "tipo": bootstrap_select(),
            "descripcion": bootstrap_input(placeholder="Notas adicionales"),
            "cantidad": bootstrap_number(),
            "unidad": bootstrap_select(),
            "precio_unitario": bootstrap_number(),
            "monto": bootstrap_number(readonly=True),
            "fecha": bootstrap_date(),
            "recibo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Garantizar que tipo muestre todos los tipos de costo disponibles
        self.fields["tipo"].queryset = TipoCosto.objects.all().order_by("nombre")
        # Monto readonly
        self.fields["monto"].disabled = True

    def clean_recibo(self):
        recibo = self.cleaned_data.get("recibo")
        if recibo:
            if recibo.size > 5 * 1024 * 1024:  # Máximo 5MB
                raise ValidationError("El archivo no puede superar 5MB.")
        return recibo

    def clean(self):
        cleaned_data = super().clean()
        unidad = cleaned_data.get("unidad")
        cantidad = cleaned_data.get("cantidad") or Decimal("0.00")
        precio = cleaned_data.get("precio_unitario") or Decimal("0.00")

        # Calcular monto automáticamente
        monto = precio if unidad == "COP" else cantidad * precio

        if monto <= 0:
            raise ValidationError("El monto del costo debe ser mayor a 0.")

        cleaned_data["monto"] = monto.quantize(Decimal("1.00"))
        return cleaned_data


# ======================
# INLINE FORMSET OPCIONAL
# ======================
from django.forms import inlineformset_factory

CostoEmbarqueFormSet = inlineformset_factory(
    Embarque,
    CostoEmbarque,
    form=CostoEmbarqueForm,
    extra=1,
    can_delete=True
)

