from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView
from .models import Pago
from .forms import PagoForm
from ventas.models import Venta
from django.db import transaction
from django.contrib import messages
from django.core.exceptions import ValidationError

class PagoListView(LoginRequiredMixin, ListView):
    model = Pago
    template_name = 'cartera/pago_list.html'
    context_object_name = 'pagos'
    
    def get_queryset(self):
        return Pago.objects.select_related('venta', 'venta__cliente').all().order_by('-fecha_creacion')

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
                # Nivel Banco: Bloqueo transaccional
                with transaction.atomic():
                    # Bloqueamos la venta relacionada para evitar que otro pague 
                    # al mismo tiempo y pise el saldo.
                    venta_obj = Venta.objects.select_for_update().get(pk=form.cleaned_data['venta'].pk)
                    
                    # Creamos la instancia sin guardar para asignar auditoría
                    pago = form.save(commit=False)
                    pago.usuario_registro = request.user
                    pago.save()
                
                messages.success(request, f"Pago de ${pago.monto} registrado exitosamente (Código Ref: {pago.referencia or 'N/A'}).")
                return redirect('ventas:detalle', pk=pago.venta.pk)
            except ValidationError as e:
                messages.error(request, f"Validación financiera fallida: {e}")
            except Exception as e:
                messages.error(request, f"Error crítico en transacción bancaria: {e}")
    else:
        form = PagoForm(initial=initial)
    
    return render(request, 'cartera/pago_form.html', {'form': form})
