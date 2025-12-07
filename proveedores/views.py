from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Proveedor


class ProveedorListView(ListView):
    model = Proveedor
    template_name = 'proveedores/proveedor_list.html'
    context_object_name = 'proveedores'
    ordering = ['nombre']


class ProveedorCreateView(CreateView):
    model = Proveedor
    # campos mínimos y actuales del modelo
    fields = ['nombre', 'identificacion', 'telefono', 'email', 'direccion', 'rut']
    template_name = 'proveedores/proveedor_form.html'
    success_url = reverse_lazy('proveedores:lista')


class ProveedorUpdateView(UpdateView):
    model = Proveedor
    fields = ['nombre', 'identificacion', 'telefono', 'email', 'direccion', 'rut']
    template_name = 'proveedores/proveedor_form.html'
    success_url = reverse_lazy('proveedores:lista')


class ProveedorDeleteView(DeleteView):
    model = Proveedor
    template_name = 'proveedores/proveedor_confirm_delete.html'
    success_url = reverse_lazy('proveedores:lista')
