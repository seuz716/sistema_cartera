from django import forms
from .models import Venta, DetalleVenta
from productos.models import Producto
from embarques.models import Embarque
from clientes.models import Cliente


class VentaForm(forms.ModelForm):
    # El número de factura se genera automáticamente; campo oculto para no editarlo
    factura = forms.CharField(required=False, widget=forms.HiddenInput())

    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(activo=True).order_by('nombre', 'apellido'),
        widget=forms.Select(attrs={
            "class": "form-select form-select-lg rounded-3 border-light-subtle shadow-sm select2-cliente",
            "id": "id_cliente",
        }),
        empty_label="— Buscar cliente —",
    )

    embarque = forms.ModelChoiceField(
        queryset=Embarque.objects.filter(estado__in=['PROGRAMADO', 'CARGANDO', 'EN_RUTA']).order_by('-fecha', '-numero'),
        widget=forms.Select(attrs={
            "class": "form-select form-select-lg rounded-3 border-light-subtle shadow-sm",
            "id": "id_embarque",
        }),
        required=True,
        empty_label="— Selecciona un embarque activo —",
    )

    class Meta:
        model = Venta
        fields = [
            'factura', 'cliente', 'fecha',
            'embarque', 'conductor', 'total_embalajes_entregados', 'total_embalajes_devueltos',
            'flete', 'descuentos', 'notas',
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm'
            }),
            'total_embalajes_entregados': forms.NumberInput(attrs={
                'class': 'form-control rounded-3 border-light-subtle shadow-sm text-center',
                'min': '0',
            }),
            'total_embalajes_devueltos': forms.NumberInput(attrs={
                'class': 'form-control rounded-3 border-light-subtle shadow-sm text-center',
                'min': '0',
            }),
            'flete': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end w-50 border-0 bg-transparent fw-bold',
                'step': '0.01', 'min': '0',
            }),
            'descuentos': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-end w-50 border-0 bg-transparent fw-bold text-danger',
                'step': '0.01', 'min': '0',
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control border-light-subtle shadow-sm',
                'rows': 3,
            }),
            'conductor': forms.TextInput(attrs={
                'class': 'form-control rounded-3 border-light-subtle shadow-sm',
                'readonly': 'readonly'
            }),
        }


class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'unidades_entregadas', 'cantidad_facturada', 'precio_unitario']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-select producto-select w-100',
                'data-placeholder': 'Seleccione o busque un producto'
            }),
            'unidades_entregadas': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'min': '1', 'step': '1',
                'placeholder': 'Ej. 5',
                'title': 'Unidades físicas entregadas'
            }),
            'cantidad_facturada': forms.NumberInput(attrs={
                'class': 'form-control rounded-3 border-light-subtle shadow-sm text-center',
                'placeholder': '0.00', 'step': '0.01', 'min': '0',
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control rounded-3 border-light-subtle shadow-sm text-end',
            }),
        }


DetalleVentaFormSet = forms.inlineformset_factory(
    Venta, DetalleVenta,
    form=DetalleVentaForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)
