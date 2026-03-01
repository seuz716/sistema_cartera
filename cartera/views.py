from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView
from .models import Pago
from ventas.models import Venta
from django import forms
from django.db import transaction
from django.contrib import messages

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
            raise forms.ValidationError(f"Operación rechazada: El pago (${monto}) excede el saldo pendiente de la factura (${venta.saldo}).")
            
        return monto

class PagoListView(LoginRequiredMixin, ListView):
    model = Pago
    template_name = 'cartera/pago_list.html'
    context_object_name = 'pagos'
    
    def get_queryset(self):
        return Pago.objects.select_related('venta', 'venta__cliente').all().order_by('-fecha_registro')

@login_required
def registrar_pago(request, venta_id=None):
    initial = {}
    if venta_id:
        venta = get_object_or_404(Venta, pk=venta_id)
        initial['venta'] = venta
        initial['monto'] = venta.saldo
    
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    pago = form.save()
                messages.success(request, f"Pago de ${pago.monto} registrado correctamente.")
                return redirect('ventas:detalle', pk=pago.venta.pk)
            except Exception as e:
                messages.error(request, f"Error al registrar pago: {e}")
    else:
        form = PagoForm(initial=initial)
    
    return render(request, 'cartera/pago_form.html', {'form': form})
