from django.urls import path
from django.shortcuts import redirect
from .views import AnalizarDatosView, ChatIAView, chat_frontend, panel_analisis

def redirect_root(request):
    return redirect("/api/ia/panel/")

urlpatterns = [
    path("", redirect_root, name="ia_root"),             # GET /api/ia → panel IA
    path("analizar/", AnalizarDatosView.as_view(), name="ia_analizar"),
    path("chat/", ChatIAView.as_view(), name="ia_chat"),
    path("panel/", chat_frontend, name="ia_panel"),
    path("analisis/", panel_analisis, name="ia_analisis"),
]
