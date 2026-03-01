from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView
from .models import Pago
from ventas.models import Venta
from django import forms

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['venta', 'fecha', 'monto', 'metodo_pago', 'pagado_por', 'referencia', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

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
            pago = form.save()
            return redirect('ventas:detalle', pk=pago.venta.pk)
    else:
        form = PagoForm(initial=initial)
    
    return render(request, 'cartera/pago_form.html', {'form': form})
