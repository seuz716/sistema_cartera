from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        # ✅ Dejamos solo los campos editables
        fields = [
            'numero_identificacion', 'tipo_persona', 'nombre', 'apellido',
            'email', 'telefono', 'direccion', 'ciudad',
            'forma_pago', 'dias_credito', 'activo'
        ]
        # ✅ El saldo tampoco debería editarse manualmente, 
        # pero si quieres mostrarlo puedes controlarlo en la plantilla
        widgets = {
            'saldo': forms.NumberInput(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Como 'saldo' no se edita manualmente, lo deshabilitamos
        if 'saldo' in self.fields:
            self.fields['saldo'].disabled = True

        # ⚠️ 'fecha_creacion' y 'fecha_actualizacion' 
        # no se incluyen porque son no editables en el modelo.
        # Si quieres mostrarlos en el formulario, puedes hacerlo así:
        if self.instance.pk:  # cuando el cliente ya existe
            self.fields['fecha_creacion_display'] = forms.DateTimeField(
                initial=self.instance.fecha_creacion,
                disabled=True,
                label="Fecha de creación"
            )
            self.fields['fecha_actualizacion_display'] = forms.DateTimeField(
                initial=self.instance.fecha_actualizacion,
                disabled=True,
                label="Última actualización"
            )
