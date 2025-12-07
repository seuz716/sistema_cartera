# recoleccion/urls.py
from django.urls import path
from . import views

app_name = 'recoleccion'

urlpatterns = [
    path('', views.RecoleccionListView.as_view(), name='lista'),
    path('nuevo/', views.RecoleccionCreateView.as_view(), name='crear'),
    path('rutas/', views.RutaListView.as_view(), name='rutas'),
    path('proveedores/', views.ProveedorListView.as_view(), name='proveedores'),
]
