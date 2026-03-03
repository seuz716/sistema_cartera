from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from .models import Embarque, GastoEmbarque, NovedadEmbarque
from .forms import EmbarqueForm, EmbarqueCargaFormSet, GastoEmbarqueForm, NovedadEmbarqueForm


# ========================
# VISTAS DE EMBARQUES
# ========================
class EmbarqueListView(LoginRequiredMixin, ListView):
    model = Embarque
    template_name = "embarques/embarque_list.html"
    context_object_name = "embarques"
    paginate_by = 20


class EmbarqueDetailView(LoginRequiredMixin, DetailView):
    model = Embarque
    template_name = "embarques/embarque_detail.html"
    context_object_name = "embarque"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["gastos"] = self.object.gastos.all()
        context["carga"] = self.object.items.all()
        context["novedades"] = self.object.novedades.all().select_related('producto')
        context["inventario_transito"] = self.object.obtener_inventario_transito()
        return context



class NovedadEmbarqueCreateView(LoginRequiredMixin, CreateView):
    model = NovedadEmbarque
    form_class = NovedadEmbarqueForm
    template_name = "embarques/generic_form.html"

    def form_valid(self, form):
        form.instance.embarque = get_object_or_404(Embarque, pk=self.kwargs["pk"])
        messages.success(self.request, "Novedad registrada.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("embarques:detalle", args=[self.kwargs["pk"]])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Registrar Novedad (Conciliación)"
        return context


class EmbarqueFormsetMixin:
    """Mixin para manejar el formset de carga en Create/Update."""
    def get_context_data(self, **kwargs):
        from productos.models import Producto
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["carga_formset"] = EmbarqueCargaFormSet(self.request.POST, instance=self.object)
        else:
            data["carga_formset"] = EmbarqueCargaFormSet(instance=self.object)
        
        # Datos para el JS de la plantilla
        data["productos_list"] = Producto.objects.filter(activo=True).values('id', 'tipo_medida') or []
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        carga_formset = context["carga_formset"]
        with transaction.atomic():
            self.object = form.save(commit=False)
            if not self.object.pk:
                self.object.usuario_registro = self.request.user
            self.object.save()
            
            if carga_formset.is_valid():
                carga_formset.instance = self.object
                carga_formset.save()
                # Recalcular peso inicial después de guardar la carga
                self.object.calcular_peso_total()
                self.object.save()
            else:
                return self.render_to_response(self.get_context_data(form=form))
                
        messages.success(self.request, "Embarque guardado correctamente.")
        return redirect(self.get_success_url())


class EmbarqueCreateView(LoginRequiredMixin, EmbarqueFormsetMixin, CreateView):
    model = Embarque
    form_class = EmbarqueForm
    template_name = "embarques/embarque_form.html"

    def get_success_url(self):
        return reverse("embarques:detalle", args=[self.object.pk])


class EmbarqueUpdateView(LoginRequiredMixin, EmbarqueFormsetMixin, UpdateView):
    model = Embarque
    form_class = EmbarqueForm
    template_name = "embarques/embarque_form.html"

    def get_success_url(self):
        return reverse("embarques:detalle", args=[self.object.pk])


class EmbarqueDeleteView(LoginRequiredMixin, DeleteView):
    model = Embarque
    template_name = "embarques/embarque_confirm_delete.html"
    success_url = reverse_lazy("embarques:lista")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Embarque eliminado exitosamente.")
        return super().delete(request, *args, **kwargs)


# ========================
# VISTAS DE TIPO EMBALAJE
# ========================
from .models import TipoEmbalaje, Transportador, Ruta, Vehiculo
from .forms import TipoEmbalajeForm, TransportadorForm, RutaForm, VehiculoForm

class TipoEmbalajeCreateView(LoginRequiredMixin, CreateView):
    model = TipoEmbalaje
    form_class = TipoEmbalajeForm
    template_name = "embarques/generic_form.html"
    success_url = reverse_lazy("embarques:crear")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo Tipo de Embalaje"
        return context

class TransportadorCreateView(LoginRequiredMixin, CreateView):
    model = Transportador
    form_class = TransportadorForm
    template_name = "embarques/generic_form.html"
    success_url = reverse_lazy("embarques:crear")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo Transportador"
        return context

class RutaCreateView(LoginRequiredMixin, CreateView):
    model = Ruta
    form_class = RutaForm
    template_name = "embarques/ruta_form.html"
    success_url = reverse_lazy("embarques:crear")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nueva Ruta"
        return context

class VehiculoCreateView(LoginRequiredMixin, CreateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = "embarques/generic_form.html"
    success_url = reverse_lazy("embarques:crear")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo Vehículo"
        return context
