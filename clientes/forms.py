from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'numero_identificacion',
            'tipo_persona',
            'nombre',
            'apellido',
            'email',
            'telefono',
            'direccion',
            'ciudad',
            'forma_pago',
            'dias_credito',
            'saldo',
            'activo',
        ]
        widgets = {
            'numero_identificacion': forms.TextInput(attrs={'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm', 'placeholder': 'Ej: 1312345678'}),
            'tipo_persona': forms.Select(attrs={'class': 'form-select form-select-lg rounded-3 border-light-subtle shadow-sm'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm', 'placeholder': 'Juan Alberto'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm', 'placeholder': 'Pérez García'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm', 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm', 'placeholder': '+593 ...'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm', 'placeholder': 'Calle ..., Av. ...'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm', 'placeholder': 'Quito, Guayaquil, etc.'}),
            'forma_pago': forms.Select(attrs={'class': 'form-select form-select-lg rounded-3 border-light-subtle shadow-sm'}),
            'dias_credito': forms.NumberInput(attrs={'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm'}),
            'saldo': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control form-control-lg rounded-3 bg-light text-muted border-light-subtle shadow-sm'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input ms-0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'saldo' in self.fields:
            self.fields['saldo'].disabled = True
