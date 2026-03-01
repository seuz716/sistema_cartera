from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.VentaListView.as_view(), name='lista'),
    path('historico/', views.VentaHistoricoListView.as_view(), name='historico'),
    path('nueva/', views.venta_create, name='crear'),
    path('<int:pk>/', views.VentaDetailView.as_view(), name='detalle'),
]
