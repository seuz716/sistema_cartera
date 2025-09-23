from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages

from .models import Producto
from .forms import ProductoForm


# ✅ Listado de productos
class ProductoListView(ListView):
    model = Producto
    template_name = "productos/producto_list.html"
    context_object_name = "productos"
    paginate_by = 20  # opcional, por si hay muchos productos

    def get_queryset(self):
        """Permite filtrar productos activos únicamente"""
        return Producto.objects.filter(activo=True).order_by("nombre")


# ✅ Crear nuevo producto
class ProductoCreateView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = "productos/producto_form.html"
    success_url = reverse_lazy("productos:lista")

    def form_valid(self, form):
        """Se ejecuta si el formulario es válido"""
        try:
            messages.success(self.request, "✅ Producto creado correctamente.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"❌ Error al crear producto: {e}")
            return super().form_invalid(form)


# ✅ Editar producto
class ProductoUpdateView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = "productos/producto_form.html"
    success_url = reverse_lazy("productos:lista")

    def form_valid(self, form):
        try:
            messages.success(self.request, "✏️ Producto actualizado correctamente.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"❌ Error al actualizar producto: {e}")
            return super().form_invalid(form)


# ✅ Eliminar producto
class ProductoDeleteView(DeleteView):
    model = Producto
    template_name = "productos/producto_confirm_delete.html"
    success_url = reverse_lazy("productos:lista")

    def delete(self, request, *args, **kwargs):
        """Elimina el producto de forma segura"""
        try:
            messages.success(request, "🗑️ Producto eliminado correctamente.")
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f"❌ Error al eliminar producto: {e}")
            return redirect("productos:lista")
