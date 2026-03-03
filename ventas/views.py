from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Sum
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse

from .models import Venta, DetalleVenta, ConfiguracionFactura, generar_consecutivo
from productos.models import Producto
from .forms import VentaForm, DetalleVentaFormSet
from embarques.models import Embarque


# ─────────────────────────────────────────────
# LISTADOS
# ─────────────────────────────────────────────

class VentaListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = 'ventas/venta_list.html'
    context_object_name = 'ventas'

    def get_queryset(self):
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


# ─────────────────────────────────────────────
# CONFIGURACIÓN DE FACTURAS (primer uso)
# ─────────────────────────────────────────────

@login_required
def configurar_facturas(request):
    """
    Vista de configuración inicial del consecutivo.
    Solo se muestra si aún no existe una ConfiguracionFactura.
    """
    from django import forms as dj_forms

    class ConfigForm(dj_forms.Form):
        prefijo = dj_forms.CharField(
            max_length=10,
            initial='FV',
            label='Prefijo de factura',
            help_text='Ej: FV, FAC, INV',
            widget=dj_forms.TextInput(attrs={'class': 'form-control form-control-lg'})
        )
        numero_inicio = dj_forms.IntegerField(
            min_value=1,
            initial=1,
            label='Número inicial del consecutivo',
            help_text='La primera factura usará este número (Ej: 1500 → FV1500)',
            widget=dj_forms.NumberInput(attrs={'class': 'form-control form-control-lg'})
        )

    config = ConfiguracionFactura.objects.filter(pk=1).first()

    if request.method == 'POST':
        form = ConfigForm(request.POST)
        if form.is_valid():
            if config:
                config.prefijo = form.cleaned_data['prefijo']
                config.numero_inicio = form.cleaned_data['numero_inicio']
                config.save()
            else:
                ConfiguracionFactura.objects.create(
                    pk=1,
                    prefijo=form.cleaned_data['prefijo'],
                    numero_inicio=form.cleaned_data['numero_inicio']
                )
            messages.success(request, f"Configuración guardada. Las facturas empezarán en "
                                       f"{form.cleaned_data['prefijo']}{form.cleaned_data['numero_inicio']}.")
            return redirect('ventas:crear')
    else:
        initial = {'prefijo': config.prefijo, 'numero_inicio': config.numero_inicio} if config else {}
        form = ConfigForm(initial=initial)

    return render(request, 'ventas/configurar_facturas.html', {'form': form, 'config': config})


# ─────────────────────────────────────────────
# AJAX: datos del embarque
# ─────────────────────────────────────────────

@login_required
def embarque_conductor_json(request, pk):
    """
    Devuelve conductor, vehículo y placa del embarque seleccionado.
    Usado por el JS del formulario para auto-llenar el campo conductor.
    """
    embarque = get_object_or_404(Embarque, pk=pk)
    return JsonResponse({
        'conductor': embarque.conductor or '',
        'vehiculo': str(embarque.vehiculo) if embarque.vehiculo else '',
        'placa': embarque.vehiculo.placa if embarque.vehiculo else '',
    })


@login_required
def producto_empaque_json(request, pk):
    """
    Devuelve la capacidad de embalaje por defecto del producto.
    """
    from embarques.models import CapacidadEmbalaje
    capacidad = CapacidadEmbalaje.objects.filter(producto_id=pk).first()
    return JsonResponse({
        'unidades_por_paquete': capacidad.unidades_por_paquete if capacidad else 0
    })


# ─────────────────────────────────────────────
# CREAR VENTA
# ─────────────────────────────────────────────

@login_required
def venta_create(request):
    # Verificar si hay configuración; si no, redirigir a configurarla
    if not ConfiguracionFactura.objects.filter(pk=1).exists():
        messages.info(request, "Por favor configure el prefijo y número inicial de facturas antes de continuar.")
        return redirect('ventas:configurar_facturas')

    if request.method == 'POST':
        form = VentaForm(request.POST)
        formset = DetalleVentaFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            descuentos = form.cleaned_data.get('descuentos') or 0
            flete = form.cleaned_data.get('flete') or 0

            subtotal_calculado = sum(
                (f.cleaned_data.get('cantidad_facturada', 0) or 0) * (f.cleaned_data.get('precio_unitario', 0) or 0)
                for f in formset.forms
                if hasattr(f, 'cleaned_data') and f.cleaned_data and not f.cleaned_data.get('DELETE')
            )

            if descuentos > subtotal_calculado:
                messages.error(
                    request,
                    f"Error: Los descuentos (${descuentos}) no pueden ser mayores que el subtotal (${subtotal_calculado})."
                )
            else:
                try:
                    with transaction.atomic():
                        venta = form.save(commit=False)

                        # 1. Asignar consecutivo automático
                        venta.factura = generar_consecutivo()

                        # 2. Snapshot de datos del embarque (Nivel Banco: Persistencia histórica)
                        if venta.embarque:
                            # Preferimos los datos del embarque si no se ingresaron manual (aunque el form los ponga readonly)
                            venta.conductor = venta.embarque.conductor
                            if venta.embarque.vehiculo:
                                venta.placa = venta.embarque.vehiculo.placa

                        venta.save()
                        formset.instance = venta
                        formset.save()

                        # 3. Recalcular totales finales
                        venta.actualizar_totales()

                    messages.success(request, f"✅ Factura {venta.factura} creada exitosamente.")
                    return redirect('ventas:detalle', pk=venta.pk)

                except Exception as e:
                    messages.error(request, f"Error crítico al guardar la factura: {str(e)}")
        else:
            # Informar al usuario específicamente por qué no se procesó
            if not form.is_valid():
                messages.error(request, "Por favor corrija los errores en el encabezado de la factura.")
            if not formset.is_valid():
                messages.error(request, "Hay errores en los productos detallados (verifique cantidades y precios).")
    else:
        form = VentaForm()
        formset = DetalleVentaFormSet()

    proxima_factura = generar_consecutivo()

    return render(request, 'ventas/venta_form.html', {
        'form': form,
        'formset': formset,
        'proxima_factura': proxima_factura,
        'productos_list': Producto.objects.filter(activo=True),
    })
