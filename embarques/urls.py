from django.urls import path
from . import views

app_name = "embarques"

urlpatterns = [
    # -----------------------
    # EMBARQUES
    # -----------------------
    path("", views.EmbarqueListView.as_view(), name="lista"),
    path("nuevo/", views.EmbarqueCreateView.as_view(), name="crear"),
    path("<int:pk>/", views.EmbarqueDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.EmbarqueUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", views.EmbarqueDeleteView.as_view(), name="eliminar"),

    # -----------------------
    # COSTOS DE EMBARQUE
    # -----------------------
    path(
        "<int:embarque_id>/costos/nuevo/",
        views.CostoCrearView.as_view(),
        name="costo_crear"
    ),
    path(
        "costos/<int:pk>/editar/",
        views.CostoUpdateView.as_view(),
        name="costo_editar"
    ),
    path(
        "costos/<int:pk>/eliminar/",
        views.CostoDeleteView.as_view(),
        name="costo_eliminar"
    ),
]
