from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

from .models import Embarque, CostoEmbarque
from .forms import EmbarqueForm, CostoEmbarqueForm

# ========================
# VISTAS DE EMBARQUES
# ========================
class EmbarqueListView(ListView):
    model = Embarque
    template_name = "embarques/embarque_list.html"
    context_object_name = "embarques"
    paginate_by = 20


class EmbarqueDetailView(DetailView):
    model = Embarque
    template_name = "embarques/embarque_detail.html"
    context_object_name = "embarque"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["costos"] = self.object.costos.select_related("tipo")
        context["costo_total"] = self.object.costo_total
        return context


class EmbarqueCreateView(CreateView):
    model = Embarque
    form_class = EmbarqueForm
    template_name = "embarques/embarque_form.html"

    def form_valid(self, form):
        # usar manager custom para asegurar número único
        self.object = Embarque.objects.crear_unico(
            fecha=form.cleaned_data.get("fecha"),
            conductor=form.cleaned_data.get("conductor"),
            vehiculo=form.cleaned_data.get("vehiculo"),
            placa=form.cleaned_data.get("placa"),
        )
        messages.success(self.request, f"Embarque {self.object.numero} creado exitosamente.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("embarques:detalle", args=[self.object.pk])


class EmbarqueUpdateView(UpdateView):
    model = Embarque
    form_class = EmbarqueForm
    template_name = "embarques/embarque_form.html"

    def get_success_url(self):
        messages.success(self.request, "Embarque actualizado correctamente.")
        return reverse("embarques:detalle", args=[self.object.pk])


class EmbarqueDeleteView(DeleteView):
    model = Embarque
    template_name = "embarques/embarque_confirm_delete.html"
    success_url = reverse_lazy("embarques:lista")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Embarque eliminado exitosamente.")
        return super().delete(request, *args, **kwargs)


# ========================
# Mixin para Vistas de COSTOS
# ========================
class CostoMixin:
    model = CostoEmbarque
    form_class = CostoEmbarqueForm
    template_name = "embarques/costo_form.html"

    def get_embarque(self):
        """
        Obtiene el embarque relacionado con el costo.
        Funciona tanto para creación como edición/eliminación.
        """
        # Para Update/Delete: el objeto ya existe
        if hasattr(self, 'object') and self.object is not None:
            return self.object.embarque
        # Para Create: obtener desde kwargs
        embarque_id = self.kwargs.get("embarque_id")
        if embarque_id:
            return get_object_or_404(Embarque, pk=embarque_id)
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["embarque"] = self.get_embarque()
        return context

    def form_valid(self, form):
        form.instance.embarque = self.get_embarque()
        messages.success(self.request, "Costo guardado exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        embarque = self.get_embarque()
        if embarque:
            return reverse("embarques:detalle", args=[embarque.pk])
        return reverse("embarques:lista")


# ========================
# VISTAS DE COSTOS
# ========================
class CostoCrearView(CostoMixin, CreateView):
    pass


class CostoUpdateView(CostoMixin, UpdateView):
    pass


class CostoDeleteView(DeleteView):
    model = CostoEmbarque
    template_name = "embarques/costo_confirm_delete.html"

    def get_success_url(self):
        embarque = self.object.embarque
        messages.success(self.request, "Costo eliminado correctamente.")
        return reverse("embarques:detalle", args=[embarque.pk])
