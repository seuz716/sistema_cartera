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
    path("<int:pk>/novedad/", views.NovedadEmbarqueCreateView.as_view(), name="novedad_crear"),
    path("<int:pk>/editar/", views.EmbarqueUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", views.EmbarqueDeleteView.as_view(), name="eliminar"),

    # -----------------------
    # INFRAESTRUCTURA
    # -----------------------
    path("embalajes/nuevo/", views.TipoEmbalajeCreateView.as_view(), name="embalaje_crear"),
    path("transportadores/nuevo/", views.TransportadorCreateView.as_view(), name="transportador_crear"),
    path("rutas/nuevo/", views.RutaCreateView.as_view(), name="ruta_crear"),
    path("vehiculos/nuevo/", views.VehiculoCreateView.as_view(), name="vehiculo_crear"),
]
