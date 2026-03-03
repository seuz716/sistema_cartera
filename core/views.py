from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from clientes.models import Cliente
from ventas.models import Venta
from cartera.models import Pago
from django.db.models import Sum

from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
import json

@login_required
def home(request):
    # Rango de tiempo: últimos 30 días
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    # Datos de Ventas (últimos 30 días)
    ventas_data = Venta.objects.filter(fecha__gte=hace_30_dias)\
        .values('fecha')\
        .annotate(total=Sum('total_con_flete'))\
        .order_by('fecha')
    
    # Datos de Pagos (últimos 30 días)
    pagos_data = Pago.objects.filter(fecha__gte=hace_30_dias)\
        .values('fecha')\
        .annotate(total=Sum('monto'))\
        .order_by('fecha')

    # Preparar labels (días) y datasets para ApexCharts (JSON)
    labels = []
    ventas_vals = []
    pagos_vals = []
    
    # Mapear datos a un diccionario para facilitar el llenado de huecos
    dict_ventas = {d['fecha'].strftime('%Y-%m-%d'): float(d['total']) for d in ventas_data}
    dict_pagos = {d['fecha'].strftime('%Y-%m-%d'): float(d['total']) for d in pagos_data}
    
    for i in range(30, -1, -1):
        dia = hoy - timedelta(days=i)
        dia_str = dia.strftime('%Y-%m-%d')
        labels.append(dia_str)
        ventas_vals.append(dict_ventas.get(dia_str, 0))
        pagos_vals.append(dict_pagos.get(dia_str, 0))

    context = {
        'total_clientes': Cliente.objects.count(),
        'total_saldo': Venta.objects.aggregate(Sum('saldo'))['saldo__sum'] or 0,
        'total_recaudado': Pago.objects.aggregate(Sum('monto'))['monto__sum'] or 0,
        'chart_labels': json.dumps(labels),
        'chart_ventas': json.dumps(ventas_vals),
        'chart_pagos': json.dumps(pagos_vals),
    }
    return render(request, 'core/home.html', context)
