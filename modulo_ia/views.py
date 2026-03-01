from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
# from django.views.decorators.csrf import csrf_exempt  # Eliminado por seguridad
# from django.utils.decorators import method_decorator

# REST Framework imports (faltaban)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import json
import os

from google import genai

# Importar tu servicio
from .gemini_service import GeminiAIService

# Importar token manager
from .token_manager import count_tokens, can_use, remaining_tokens, register_tokens, smart_truncate

# El cliente se inicializa preferiblemente a través de GeminiAIService o con entorno seguro
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
genai_client = None

if GEMINI_KEY:
    try:
        genai_client = genai.Client(api_key=GEMINI_KEY)
    except Exception:
        genai_client = None


# -----------------------------------------
#         RENDERS DEL FRONTEND
# -----------------------------------------

@login_required
def panel_analisis(request):
    return render(request, "modulo_ia/analisis.html")


@login_required
def chat_frontend(request):
    return render(request, "modulo_ia/chat.html")


# -----------------------------------------
#     VISTA PARA ANALIZAR DATOS
# -----------------------------------------

class AnalizarDatosView(LoginRequiredMixin, View):
    """
    Vista funcional para analizar datos usando JSON estándar.
    """
    def post(self, request):
        try:
            body = json.loads(request.body)
            data_context = body.get("data", "")

            ai = GeminiAIService()
            result = ai.analyze_data(data_context)

            return JsonResponse({"result": result})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# -----------------------------------------
#     CHAT IA CON CONTROL DE TOKENS
# -----------------------------------------

class ChatIAView(LoginRequiredMixin, View):
    """
    Chat interactivo con control de tokens y respuesta en tiempo real.
    """
    def post(self, request):
        try:
            body = json.loads(request.body)
            msg = body.get("message", "")
            
            ai = GeminiAIService()
            # Si no hay cliente, devolvemos error amigable
            if not ai.client:
                return JsonResponse({
                    "error": "Servicio de IA no disponible: GEMINI_API_KEY no configurada en el archivo .env"
                }, status=500)

            # ---- Truncado inteligente si es muy largo ----
            msg = smart_truncate(msg, max_tokens=2000, client=ai.client)

            # ---- Control de tokens reales ----
            tokens_needed = count_tokens(msg, client=ai.client)

            if not can_use(tokens_needed):
                return JsonResponse({
                    "error": "Límite diario de tokens alcanzado.",
                    "remaining": remaining_tokens()
                }, status=429)

            # Registrar consumo del input
            register_tokens(tokens_needed, method="real")

            reply = ai.chat_response(msg)

            output_tokens = count_tokens(reply, client=ai.client)

            # Registrar tokens generados por IA
            register_tokens(output_tokens, method="real")

            return JsonResponse({"reply": reply})

        except Exception as e:
            return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)
