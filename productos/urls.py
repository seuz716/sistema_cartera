from django.urls import path
from .views import (
    ProductoListView, ProductoCreateView, ProductoUpdateView, ProductoDeleteView
)

app_name = "productos"

urlpatterns = [
    path("", ProductoListView.as_view(), name="lista"),
    path("crear/", ProductoCreateView.as_view(), name="crear"),
    path("editar/<int:pk>/", ProductoUpdateView.as_view(), name="editar"),
    path("eliminar/<int:pk>/", ProductoDeleteView.as_view(), name="eliminar"),
]
