import os
import django
import sys
from django.db.models import Sum
from decimal import Decimal

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from productos.models import Producto, MovimientoInventario
from embarques.models import EmbarqueItem, NovedadEmbarque
from ventas.models import DetalleVenta

def check_conservation_law():
    """
    Validates: Total Purchases = Stock_Warehouse + Stock_Transit + Sold + Waste (Mermas)
    """
    print("📋 AUDITORÍA: Ley de Conservación Global de Inventario")
    print("-" * 50)
    
    results = []
    
    for p in Producto.objects.all():
        # Purchases (Input to Warehouse)
        # Note: 'compra' adds to stock_actual. 
        # 'ajuste_merma' without embarque subtracts from stock_actual. 
        # But we want the total quantity that "entered" vs "where it is now".
        
        sum_compras = MovimientoInventario.objects.filter(
            producto=p, tipo__in=['compra', 'ajuste_positivo']
        ).aggregate(
            und=Sum('cantidad_unidades'), 
            kg=Sum('cantidad_kg'), 
            lts=Sum('cantidad_litros')
        )
        
        # Determine current state
        warehouse_stock = p.stock_actual
        
        transit_stock_agg = EmbarqueItem.objects.filter(producto=p).aggregate(
            und=Sum('cantidad_disponible_unidades'),
            kg=Sum('cantidad_disponible_kg'),
            lts=Sum('cantidad_disponible_litros')
        )
        
        sold_stock_agg = DetalleVenta.objects.filter(producto=p).aggregate(
            und=Sum('cantidad_unidades'),
            kg=Sum('cantidad_kg'),
            lts=Sum('cantidad_litros')
        )
        
        waste_stock_agg = NovedadEmbarque.objects.filter(
            producto=p, tipo__in=['ajuste_merma', 'daño', 'ajuste_diferencia']
        ).aggregate(
            und=Sum('cantidad_unidades'),
            kg=Sum('cantidad_kg'),
            lts=Sum('cantidad_litros')
        )
        
        # Calculate totals per unit type
        if p.tipo_medida == 'kg':
            purchased = sum_compras['kg'] or Decimal('0')
            current = (
                warehouse_stock + 
                (transit_stock_agg['kg'] or Decimal('0')) + 
                (sold_stock_agg['kg'] or Decimal('0')) + 
                (waste_stock_agg['kg'] or Decimal('0'))
            )
        elif p.tipo_medida == 'litro':
            purchased = sum_compras['lts'] or Decimal('0')
            current = (
                warehouse_stock + 
                (transit_stock_agg['lts'] or Decimal('0')) + 
                (sold_stock_agg['lts'] or Decimal('0')) + 
                (waste_stock_agg['lts'] or Decimal('0'))
            )
        else:
            purchased = sum_compras['und'] or Decimal('0')
            current = (
                warehouse_stock + 
                (transit_stock_agg['und'] or Decimal('0')) + 
                (sold_stock_agg['und'] or Decimal('0')) + 
                (waste_stock_agg['und'] or Decimal('0'))
            )
            
        diff = purchased - current
        results.append({
            'nombre': p.nombre,
            'purchased': purchased,
            'warehouse': warehouse_stock,
            'transit': transit_stock_agg['kg' if p.tipo_medida=='kg' else ('lts' if p.tipo_medida=='litro' else 'und')] or Decimal('0'),
            'sold': sold_stock_agg['kg' if p.tipo_medida=='kg' else ('lts' if p.tipo_medida=='litro' else 'und')] or Decimal('0'),
            'waste': waste_stock_agg['kg' if p.tipo_medida=='kg' else ('lts' if p.tipo_medida=='litro' else 'und')] or Decimal('0'),
            'diff': diff,
            'status': '✅ OK' if abs(diff) < Decimal('0.001') else '❌ ERROR'
        })

    # Print Report
    header = "| Producto | Compras | Almacén | Tránsito | Vendido | Merma | Dif. | Estado |"
    sep = "|---|---:|---:|---:|---:|---:|---:|:---:|"
    print(header)
    print(sep)
    for r in results:
        print(f"| {r['nombre']} | {r['purchased']:,.2f} | {r['warehouse']:,.2f} | {r['transit']:,.2f} | {r['sold']:,.2f} | {r['waste']:,.2f} | {r['diff']:,.2f} | {r['status']} |")

if __name__ == "__main__":
    check_conservation_law()
