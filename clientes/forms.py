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
            'saldo': forms.NumberInput(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'saldo' in self.fields:
            self.fields['saldo'].disabled = True
