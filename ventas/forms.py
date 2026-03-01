from django.db import models
from django import forms
from .models import Venta, DetalleVenta
from productos.models import Producto

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['factura', 'cliente', 'fecha', 'embarque', 'conductor', 'flete', 'descuentos', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario']

DetalleVentaFormSet = forms.inlineformset_factory(
    Venta, DetalleVenta,
    form=DetalleVentaForm,
    extra=1,
    can_delete=True
)
