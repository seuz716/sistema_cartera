import os
import django
import sys
from decimal import Decimal

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ventas.models import Venta, DetalleVenta
from productos.models import Producto

def audit_facturas():
    ventas = Venta.objects.all().prefetch_related('detalles', 'detalles__producto')
    
    headers = [
        "Factura", "Can. Crema", "Und. Crema", "$ Crema",
        "Can. Cuajada", "Kg Cuajada", "$ Cuajada",
        "Kg Mant.", "$ Mant.", "Tajado", "Desc.", "Flete",
        "Total (S.F.)", "Total (C.F.)", "Kg Prom. Cuajada"
    ]
    
    results = []

    for v in ventas:
        can_crema = Decimal('0')
        und_crema = Decimal('0')
        precio_v_crema = Decimal('0')
        
        can_cuajada = Decimal('0')
        kg_cuajada = Decimal('0')
        precio_v_cuajada = Decimal('0')
        
        kg_mant = Decimal('0')
        precio_v_mant = Decimal('0')
        
        costo_tajado = Decimal('0')
        
        for d in v.detalles.all():
            nombre = d.producto.nombre.upper() if d.producto.nombre else ""
            
            # Tajado: Suma de (precio_tajado_unidad * cantidad_unidades)
            if d.tajado:
                # El usuario pide "- tajado" en la formula total.
                # Calculamos el costo total del servicio de tajado.
                qty = d.cantidad_unidades or Decimal('0')
                costo_tajado += (d.precio_tajado_unidad or Decimal('0')) * qty

            if 'CREMA' in nombre and 'DOBLE' in nombre:
                c = Decimal(str(d.embalajes_entregados or 0))
                can_crema += c
                # Regla 1: unidades crema = canastillas crema * 16
                und_item = c * 16
                und_crema += und_item
                # Regla 2: precio total crema = unidades crema * precio unidad crema
                precio_v_crema += und_item * d.precio_unitario
                
            elif 'CUAJADA' in nombre:
                c = Decimal(str(d.embalajes_entregados or 0))
                can_cuajada += c
                kg = d.cantidad_kg or Decimal('0')
                kg_cuajada += kg
                # Regla 3: precio total cuajada = peso canastillas cuajada * precio kg cuajada
                precio_v_cuajada += kg * d.precio_unitario
                
            elif 'MANTEQUILLA' in nombre:
                kg = d.cantidad_kg or Decimal('0')
                kg_mant += kg
                # Regla 4: precio total mantequilla = peso mantequilla * precio unidad mantequilla
                precio_v_mant += kg * d.precio_unitario

        # Regla 5: total factura sin flete = crema + cuajada + mantequilla - descuentos - tajado
        total_sf = precio_v_crema + precio_v_cuajada + precio_v_mant - v.descuentos - costo_tajado
        
        # Regla 6: total factura flete descontado = total factura sin flete - flete
        total_cf = total_sf - v.flete
        
        # Regla 7: kg promedio cuajada = peso canastillas cuajada / canastillas cuajada
        kg_prom = (kg_cuajada / can_cuajada) if can_cuajada > 0 else Decimal('0')
        
        results.append([
            v.factura,
            f"{can_crema:,.2f}",
            f"{und_crema:,.2f}",
            f"{precio_v_crema:,.2f}",
            f"{can_cuajada:,.2f}",
            f"{kg_cuajada:,.2f}",
            f"{precio_v_cuajada:,.2f}",
            f"{kg_mant:,.2f}",
            f"{precio_v_mant:,.2f}",
            f"{costo_tajado:,.2f}",
            f"{v.descuentos:,.2f}",
            f"{v.flete:,.2f}",
            f"{total_sf:,.2f}",
            f"{total_cf:,.2f}",
            f"{kg_prom:,.2f}"
        ])

    if not results:
        print("No se encontraron facturas.")
        return

    # Determinamos anchos de columna para formato de tabla compatible con Markdown si es posible
    col_widths = [max(len(str(row[i])) for row in [headers] + results) for i in range(len(headers))]
    
    def print_row(row):
        print("| " + " | ".join(str(val).rjust(col_widths[i]) for i, val in enumerate(row)) + " |")

    # Imprimir en formato Markdown para que sea renderizado en el chat
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join("-" * (len(h) + 2) for h in headers) + "|")
    # Para Markdown real, los separadores deben ser así:
    sep = "|" + "|".join("---" for _ in headers) + "|"
    # Reinicio para asegurar formato Markdown correcto
    print("| " + " | ".join(headers) + " |")
    print(sep)
    for r in results:
        print("| " + " | ".join(r) + " |")

if __name__ == "__main__":
    audit_facturas()
