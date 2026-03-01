from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from clientes.models import Cliente
from ventas.models import Venta
from cartera.models import Pago
from django.db.models import Sum

@login_required
def home(request):
    context = {
        'total_clientes': Cliente.objects.count(),
        'total_saldo': Venta.objects.aggregate(Sum('saldo'))['saldo__sum'] or 0,
        'total_recaudado': Pago.objects.aggregate(Sum('monto'))['monto__sum'] or 0,
    }
    return render(request, 'core/home.html', context)
