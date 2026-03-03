from django.urls import path
from . import views

app_name = 'cartera'

urlpatterns = [
    path('pagos/', views.PagoListView.as_view(), name='lista'),
    path('pagos/nuevo/', views.registrar_pago, name='crear'),
    path('pagos/nuevo/<int:venta_id>/', views.registrar_pago, name='crear_venta'),
    path('recibo/nuevo/', views.registrar_recibo_caja, name='registrar_recibo'),
]
