from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.VentaListView.as_view(), name='lista'),
    path('historico/', views.VentaHistoricoListView.as_view(), name='historico'),
    path('nueva/', views.venta_create, name='crear'),
    path('configurar/', views.configurar_facturas, name='configurar_facturas'),
    path('<int:pk>/', views.VentaDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.venta_update, name='editar'),
    # AJAX: datos del embarque (conductor, vehículo, placa, inventario)
    path('api/embarque/<int:pk>/conductor/', views.embarque_conductor_json, name='embarque_conductor'),
    path('api/embarque/<int:pk>/inventario/', views.embarque_inventario_json, name='embarque_inventario'),
    path('api/producto/<int:pk>/empaque/', views.producto_empaque_json, name='producto_empaque'),
]
