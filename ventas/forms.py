from django import forms
from .models import Venta, DetalleVenta
from productos.models import Producto

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['factura', 'cliente', 'fecha', 'embarque', 'conductor', 'flete', 'descuentos', 'notas']
        widgets = {
            'factura': forms.TextInput(attrs={'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm', 'placeholder': 'Ej: F-001'}),
            'cliente': forms.Select(attrs={'class': 'form-select form-select-lg rounded-3 border-light-subtle shadow-sm'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm'}),
            'embarque': forms.TextInput(attrs={'class': 'form-control rounded-3 border-light-subtle shadow-sm'}),
            'conductor': forms.TextInput(attrs={'class': 'form-control rounded-3 border-light-subtle shadow-sm'}),
            'flete': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end w-50 border-0 bg-transparent fw-bold'}),
            'descuentos': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end w-50 border-0 bg-transparent fw-bold text-danger'}),
            'notas': forms.Textarea(attrs={'class': 'form-control border-light-subtle shadow-sm', 'rows': 3}),
        }

class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select rounded-3 border-light-subtle shadow-sm'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control rounded-3 border-light-subtle shadow-sm text-center', 'placeholder': '0.00'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control rounded-3 border-light-subtle shadow-sm text-end', 'placeholder': '0.00'}),
        }

DetalleVentaFormSet = forms.inlineformset_factory(
    Venta, DetalleVenta,
    form=DetalleVentaForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)
