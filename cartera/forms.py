from django import forms
from .models import Pago


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['venta', 'fecha', 'monto', 'metodo_pago', 'pagado_por', 'referencia', 'notas']
        widgets = {
            'venta': forms.Select(attrs={'class': 'form-select form-select-lg rounded-3 border-light-subtle shadow-sm'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-3 border-light-subtle shadow-sm'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control form-control-lg rounded-3 text-success fw-bold border-success shadow-sm', 'placeholder': '0.00'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select rounded-3 border-light-subtle shadow-sm'}),
            'pagado_por': forms.TextInput(attrs={'class': 'form-control rounded-3 border-light-subtle shadow-sm', 'placeholder': 'Ej: Juan Pérez (Hermano)'}),
            'referencia': forms.TextInput(attrs={'class': 'form-control rounded-3 border-light-subtle shadow-sm', 'placeholder': 'Ej: Transf #12345'}),
            'notas': forms.Textarea(attrs={'class': 'form-control border-light-subtle shadow-sm', 'rows': 3}),
        }

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        venta = self.cleaned_data.get('venta')

        if monto is None:
            return monto

        if monto <= 0:
            raise forms.ValidationError("El monto del pago debe ser estrictamente mayor a 0.")

        if venta and monto > venta.saldo:
            raise forms.ValidationError(
                f"Operación rechazada: El pago (${monto}) excede el saldo pendiente de la factura (${venta.saldo})."
            )

        return monto
