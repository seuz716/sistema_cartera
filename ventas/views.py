from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Sum
from django.db import transaction
from django.contrib import messages
from .models import Venta, DetalleVenta
from .forms import VentaForm, DetalleVentaFormSet

class VentaListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = 'ventas/venta_list.html'
    context_object_name = 'ventas'

    def get_queryset(self):
        # Solo facturas con saldo pendiente
        return Venta.objects.select_related('cliente').filter(saldo__gt=0).order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        total = qs.aggregate(total=Sum('saldo'))['total'] or 0
        context['total_saldo'] = total
        return context

class VentaHistoricoListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = 'ventas/venta_historico.html'
    context_object_name = 'ventas'
    
    def get_queryset(self):
        return Venta.objects.select_related('cliente').all().order_by('-fecha')

class VentaDetailView(LoginRequiredMixin, DetailView):
    model = Venta
    template_name = 'ventas/venta_detail.html'

@login_required
def venta_create(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        formset = DetalleVentaFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            
            descuentos = form.cleaned_data.get('descuentos', 0)
            flete = form.cleaned_data.get('flete', 0)
            
            subtotal_calculado = sum(
                (f.cleaned_data.get('cantidad', 0) * f.cleaned_data.get('precio_unitario', 0)) 
                for f in formset.forms if hasattr(f, 'cleaned_data') and f.cleaned_data and not f.cleaned_data.get('DELETE')
            )
            
            if descuentos > subtotal_calculado:
                messages.error(request, f"Error: Los descuentos (${descuentos}) no pueden ser mayores que el subtotal de la venta (${subtotal_calculado}).")
            else:
                try:
                    with transaction.atomic():
                        venta = form.save()
                        formset.instance = venta
                        formset.save()
                        
                        # Actualizar totales finales tras guardar detalles
                        venta.actualizar_totales()
                    
                    messages.success(request, f"Factura {venta.factura} creada exitosamente.")
                    return redirect('ventas:detalle', pk=venta.pk)
                
                except Exception as e:
                    messages.error(request, f"Error crítico al guardar la transacción: {str(e)}")
                    
    else:
        form = VentaForm()
        formset = DetalleVentaFormSet()
    
    return render(request, 'ventas/venta_form.html', {
        'form': form,
        'formset': formset
    })
