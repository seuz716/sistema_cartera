from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from core.views import home  # si tienes una app core con la vista home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # home (si la tienes configurada en core/urls.py)
    path('clientes/', include('clientes.urls', namespace='clientes')),
    path('productos/', include('productos.urls', namespace='productos')),  # <<-- aquí agregas productos
    # path('ventas/', include('ventas.urls', namespace='ventas')),
    # path('cartera/', include('cartera.urls', namespace='cartera')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
