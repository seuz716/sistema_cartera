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
        queryset=Embarque.objects.filter(estado='transito').order_by('-fecha', '-numero'),
        widget=forms.Select(attrs={
            "class": "form-select form-select-lg rounded-3 border-light-subtle shadow-sm",
            "id": "id_embarque",
        }),
        required=True,
        empty_label="— Selecciona un embarque activo —",
    )

    fecha = forms.DateField(
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'type': 'text', 
                'class': 'form-control form-control-lg rounded-3 border-light-subtle shadow-sm',
                'id': 'id_fecha'
            }
        ),
        input_formats=['%Y-%m-%d']
    )

    class Meta:
        model = Venta
        fields = [
            'factura', 'cliente', 'fecha',
            'embarque', 'conductor', 'total_embalajes_entregados', 'total_embalajes_devueltos',
            'flete', 'flete_cobrado_al_cliente', 'descuentos', 'notas', 'total_embalajes_automatico',
        ]
        widgets = {
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
        
    def __init__(self, *args, **kwargs):
        from django.utils import timezone
        super().__init__(*args, **kwargs)
        self.fields['total_embalajes_entregados'].initial = 0
        self.fields['total_embalajes_devueltos'].initial = 0
        self.fields['total_embalajes_entregados'].required = False
        self.fields['total_embalajes_devueltos'].required = False
        # Si el usuario no desea fecha por defecto, comentar la siguiente línea:
        # if not self.instance.pk:
        #     self.fields['fecha'].initial = timezone.now().date()


class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'embarque_item', 'cantidad_unidades', 'cantidad_kg', 'cantidad_litros', 'precio_unitario', 'tajado', 'precio_tajado_unidad', 'embalajes_entregados']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-select producto-select w-100',
                'data-placeholder': 'Seleccione o busque un producto'
            }),
            'embarque_item': forms.HiddenInput(),
            'cantidad_unidades': forms.NumberInput(attrs={
                'class': 'form-control text-end qty-unidades',
                'min': '0', 'step': '1',
                'placeholder': 'Unds.',
            }),
            'cantidad_kg': forms.NumberInput(attrs={
                'class': 'form-control text-end qty-kg',
                'min': '0', 'step': '0.01',
                'placeholder': 'Kg.',
            }),
            'cantidad_litros': forms.NumberInput(attrs={
                'class': 'form-control text-end qty-litros',
                'min': '0', 'step': '0.01',
                'placeholder': 'Lts.',
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control rounded-3 border-light-subtle shadow-sm text-end',
            }),
            'tajado': forms.CheckboxInput(attrs={
                'class': 'form-check-input ms-2',
            }),
            'precio_tajado_unidad': forms.NumberInput(attrs={
                'class': 'form-control text-end small',
                'placeholder': 'V. Tajado',
                'step': '0.01'
            }),
            'embalajes_entregados': forms.NumberInput(attrs={
                'class': 'form-control text-end qty-embalajes',
                'min': '0', 'step': '1',
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
