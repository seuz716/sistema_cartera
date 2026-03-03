from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from ventas.models import Venta
from cartera.models import Pago
from clientes.models import Cliente
from embarques.models import Embarque
from productos.models import Producto
from proveedores.models import Proveedor
from recoleccion.models import Recoleccion

def build_context():
    """Extrae datos clave para el modelo IA sin saturarlo."""
    
    # 1. Datos resumidos/agregados (Estratégicos)
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    resumen_ventas = Venta.objects.filter(fecha__gte=hace_30_dias).aggregate(
        total_ventas=Sum('total'),
        conteo_ventas=Count('id_interno'),
        saldo_pendiente=Sum('saldo')
    )
    
    resumen_pagos = Pago.objects.filter(fecha__gte=hace_30_dias).aggregate(
        total_recaudado=Sum('monto'),
        conteo_pagos=Count('id')
    )

    # Top Clientes por Saldo (Riesgo)
    top_deudores = Cliente.objects.order_by('-saldo')[:7].values("nombre", "apellido", "saldo")
    
    # 2. Datos para tendencias (Ventas y Recaudo por día)
    ventas_por_dia = Venta.objects.filter(fecha__gte=hace_30_dias)\
        .values('fecha').annotate(total=Sum('total')).order_by('fecha')
    
    pagos_por_dia = Pago.objects.filter(fecha__gte=hace_30_dias)\
        .values('fecha').annotate(total=Sum('monto')).order_by('fecha')

    # 3. Top Productos vendidos (Estratégico)
    top_productos = Producto.objects.order_by('-stock_actual')[:5].values("nombre", "stock_actual")

    # 4. Muestras de datos (Detalles)
    clientes_muestras = Cliente.objects.values("numero_unico", "nombre", "apellido", "saldo")
    ventas_muestras = Venta.objects.values("id_interno", "factura", "cliente__nombre", "total", "saldo", "fecha", "estado")
    pagos_muestras = Pago.objects.values("id", "venta__factura", "monto", "fecha", "metodo_pago")
    
    # Nuevos modelos incorporados para visión 360°
    embarques = Embarque.objects.values("numero", "fecha", "conductor", "vehiculo")
    recolecciones = Recoleccion.objects.values("proveedor__nombre", "fecha", "litros")

    # Limitamos a 50 registros por entidad para no matar la cuota de tokens.
    return {
        "indicadores_30_dias": {
            "ventas_totales": resumen_ventas['total_ventas'] or 0,
            "cantidad_ventas": resumen_ventas['conteo_ventas'] or 0,
            "saldo_total_pendiente": resumen_ventas['saldo_pendiente'] or 0,
            "recaudo_total": resumen_pagos['total_recaudado'] or 0,
            "cantidad_pagos": resumen_pagos['conteo_pagos'] or 0,
        },
        "graficos": {
            "top_deudores": list(top_deudores),
            "tendencia_ventas": list(ventas_por_dia),
            "tendencia_recaudo": list(pagos_por_dia),
            "top_stock_productos": list(top_productos),
        },
        "ventas_recientes": list(ventas_muestras[:10]),
        "pagos_recientes": list(pagos_muestras[:10]),
        "recolecciones_recientes": list(recolecciones[:5]),
        "FECHA_ANALISIS": str(hoy)
    }

