from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Sum
from .models import Venta, DetalleVenta
from .forms import VentaForm, DetalleVentaFormSet

class VentaListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = 'ventas/venta_list.html'
    context_object_name = 'ventas'

    def get_queryset(self):
        # Por defecto solo mostrar las que tienen saldo (pendientes)
        return Venta.objects.select_related('cliente').filter(saldo__gt=0).order_by('-fecha')

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
            venta = form.save()
            formset.instance = venta
            formset.save()
            # Actualizar totales finales tras guardar detalles
            venta.actualizar_totales()
            return redirect('ventas:detalle', pk=venta.pk)
    else:
        form = VentaForm()
        formset = DetalleVentaFormSet()
    
    return render(request, 'ventas/venta_form.html', {
        'form': form,
        'formset': formset
    })
