# recoleccion/views.py
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import Recoleccion, Ruta
from proveedores.models import Proveedor

class RutaListView(ListView):
    model = Ruta
    template_name = 'recoleccion/ruta_list.html'
    context_object_name = 'rutas'


class ProveedorListView(ListView):
    model = Proveedor
    template_name = 'recoleccion/proveedor_list.html'
    context_object_name = 'proveedores'


class RecoleccionListView(ListView):
    model = Recoleccion
    template_name = 'recoleccion/recoleccion_list.html'
    context_object_name = 'recolecciones'
    ordering = ['-fecha']


class RecoleccionCreateView(CreateView):
    model = Recoleccion
    template_name = 'recoleccion/recoleccion_form.html'
    fields = ['proveedor', 'fecha', 'litros']
    success_url = reverse_lazy('recoleccion:lista')
