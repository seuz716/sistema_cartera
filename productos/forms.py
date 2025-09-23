from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "nombre",
            "descripcion",
            "imagen",              # 👈 nuevo campo
            "unidad_medida",
            "precio_unitario",
            "stock_actual",
            "control_inventario",
            "activo",
        ]

        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "imagen": forms.ClearableFileInput(attrs={"class": "form-control"}),  # 👈 input de imagen
            "precio_unitario": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "stock_actual": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "unidad_medida": forms.Select(attrs={"class": "form-select"}),
            "control_inventario": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
