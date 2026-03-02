from ventas.models import Venta
from cartera.models import Pago
from clientes.models import Cliente
from embarques.models import Embarque
from productos.models import Producto
from proveedores.models import Proveedor
from recoleccion.models import Recoleccion

def build_context():
    """Extrae datos clave para el modelo IA sin saturarlo."""

    clientes = Cliente.objects.values("numero_unico", "nombre", "apellido", "saldo")
    ventas = Venta.objects.values("id_interno", "factura", "cliente__nombre", "total", "saldo", "fecha", "estado")
    pagos = Pago.objects.values("id", "venta__factura", "monto", "fecha", "metodo_pago")
    
    # Nuevos modelos incorporados para visión 360°
    embarques = Embarque.objects.values("numero", "fecha", "conductor", "vehiculo")
    productos = Producto.objects.values("nombre", "precio_unitario", "unidad_medida", "stock_actual")
    proveedores = Proveedor.objects.values("nombre", "identificacion", "telefono")
    recolecciones = Recoleccion.objects.values("proveedor__nombre", "fecha", "litros")

    # Limitamos a 50 registros por entidad para no matar la cuota de tokens.
    return {
        "clientes": list(clientes[:50]),
        "ventas": list(ventas[:50]),
        "pagos": list(pagos[:50]),
        "embarques": list(embarques[:50]),
        "productos": list(productos[:50]),
        "proveedores": list(proveedores[:50]),
        "recolecciones": list(recolecciones[:50]),
    }
