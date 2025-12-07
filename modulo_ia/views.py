from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

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
from .token_manager import count_tokens, can_use, remaining_tokens, register_tokens

# Inicializar cliente Gemini
genai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


# -----------------------------------------
#         RENDERS DEL FRONTEND
# -----------------------------------------

def panel_analisis(request):
    return render(request, "modulo_ia/analisis.html")


def chat_frontend(request):
    return render(request, "modulo_ia/chat.html")


# -----------------------------------------
#     VISTA PARA ANALIZAR DATOS
# -----------------------------------------

@method_decorator(csrf_exempt, name='dispatch')
class AnalizarDatosView(View):

    def post(self, request):
        try:
            body = json.loads(request.body)
            data_context = body.get("data", "")
            complexity = body.get("complexity", "standard")

            ai = GeminiAIService()
            result = ai.analyze_data(data_context, complexity)

            return JsonResponse({"result": result}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# -----------------------------------------
#     CHAT IA CON CONTROL DE TOKENS
# -----------------------------------------

@method_decorator(csrf_exempt, name='dispatch')
class ChatIAView(APIView):

    def post(self, request):
        msg = request.data.get("message", "")

        # ---- Control de tokens ----
        tokens_needed = count_tokens(msg)

        if not can_use(tokens_needed):
            return Response({
                "error": "Límite diario de tokens alcanzado.",
                "remaining": remaining_tokens(),
                "msg": "Intenta mañana, bebé 💙"
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        try:
            # Registrar consumo del input
            register_tokens(tokens_needed)

            response = genai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=msg
            )

            reply = response.text
            output_tokens = count_tokens(reply)

            # Registrar tokens generados por IA
            register_tokens(output_tokens)

            return Response({"reply": reply})

        except Exception as e:
            return Response({"error": str(e)}, status=500)
