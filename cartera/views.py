from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView
from .models import Pago, ReciboCaja
from .forms import PagoForm, ReciboCajaForm
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

@login_required
def registrar_recibo_caja(request):
    """
    Vista para registrar un pago global y aplicarlo en cascada.
    """
    if request.method == 'POST':
        form = ReciboCajaForm(request.POST)
        if form.is_valid():
            try:
                recibo = form.save(commit=False)
                # La lógica de cascada está en el modelo
                excedente = recibo.registrar_y_distribuir(request.user)
                
                msg = f"Recibo de Caja registrado. Pago aplicado a facturas pendientes."
                if excedente > 0:
                    msg += f" Quedó un excedente de ${excedente} a favor del cliente."
                
                messages.success(request, msg)
                return redirect('cartera:lista')
            except Exception as e:
                messages.error(request, f"Error al procesar el recibo de caja: {e}")
    else:
        form = ReciboCajaForm()
    
    return render(request, 'cartera/recibo_form.html', {'form': form})
