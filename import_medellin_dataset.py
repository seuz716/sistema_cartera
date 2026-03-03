import os
import django
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientes.models import Cliente
from embarques.models import Ruta, Embarque, EmbarqueItem, TipoEmbalaje
from productos.models import Producto
from ventas.models import Venta, DetalleVenta

def get_base_products():
    # Identify canonical products
    p_crema = Producto.objects.filter(nombre__iexact='DOBLE CREMA').first()
    if not p_crema: p_crema = Producto.objects.filter(nombre__icontains='CREMA').first()
    
    p_cuajada = Producto.objects.filter(nombre__iexact='CUAJADA').first()
    if not p_cuajada: p_cuajada = Producto.objects.filter(nombre__icontains='CUAJADA').first()
    
    p_mantequilla = Producto.objects.filter(nombre__iexact='MANTEQUILLA').first()
    if not p_mantequilla: p_mantequilla = Producto.objects.filter(nombre__icontains='MANTEQUILLA').first()

    return p_crema, p_cuajada, p_mantequilla

def run():
    print("Iniciando Importación ERP Senior - V2 (Medellín Dataset)")
    
    p_crema, p_cuajada, p_mantequilla = get_base_products()
    if not p_crema or not p_cuajada or not p_mantequilla:
        print("Error: Fallo en detección de productos base. Verifique configuración de SKU.")
        return

    # Insumo de la tabla Medellin
    insumo = [
        {"ruta": "MEDELLIN", "cliente": "Lucio Arteaga", "f_emb": "25/02/2026", "f_fac": "27/02/2026", "can_cre": 0, "p_cre": 0, "can_cua": 30, "kg_cua": 1165.3, "p_cua": 11500, "peso_man": 0, "p_man": 0, "desc": 0, "flete": 0, "cond": "Edinson Cali", "taj": 0},
        {"ruta": "MEDELLIN", "cliente": "Eliecer Medell", "f_emb": "22/02/2026", "f_fac": "24/02/2026", "can_cre": 0, "p_cre": 0, "can_cua": 25, "kg_cua": 1074.6, "p_cua": 11400, "peso_man": 0, "p_man": 0, "desc": 0, "flete": 0, "cond": "Gustavo Medell", "taj": 0},
        {"ruta": "MEDELLIN", "cliente": "Cristian Medell", "f_emb": "22/02/2026", "f_fac": "24/02/2026", "can_cre": 0, "p_cre": 0, "can_cua": 0, "kg_cua": 0, "p_cua": 0, "peso_man": 80, "p_man": 16500, "desc": 0, "flete": 0, "cond": "Gustavo Medell", "taj": 0},
        {"ruta": "MEDELLIN", "cliente": "Felipe Nuevo", "f_emb": "22/02/2026", "f_fac": "24/02/2026", "can_cre": 6, "p_cre": 45000, "can_cua": 0, "kg_cua": 0, "p_cua": 0, "peso_man": 0, "p_man": 0, "desc": 0, "flete": 0, "cond": "Gustavo Medell", "taj": 0},
        {"ruta": "MEDELLIN", "cliente": "Edison Medellin", "f_emb": "22/02/2026", "f_fac": "24/02/2026", "can_cre": 6, "p_cre": 45500, "can_cua": 36, "kg_cua": 1412.0, "p_cua": 12400, "peso_man": 60, "p_man": 17000, "desc": 0, "flete": 0, "cond": "Gustavo Medell", "taj": 0},
        {"ruta": "MEDELLIN", "cliente": "Manuel Medell", "f_emb": "22/02/2026", "f_fac": "24/02/2026", "can_cre": 0, "p_cre": 0, "can_cua": 10, "kg_cua": 407.0, "p_cua": 12300, "peso_man": 0, "p_man": 0, "desc": 180000, "flete": 0, "cond": "Gustavo Medell", "taj": 0},
        {"ruta": "MEDELLIN", "cliente": "Leonardo Medell", "f_emb": "22/02/2026", "23/02/2026": "r", "can_cre": 0, "p_cre": 0, "can_cua": 103, "kg_cua": 4164.0, "p_cua": 12300, "peso_man": 0, "p_man": 0, "desc": 0, "flete": 0, "cond": "Gustavo Medell", "taj": 0, "f_fac": "23/02/2026"},
        {"ruta": "MEDELLIN", "cliente": "Fabian Manizal", "f_emb": "22/02/2026", "f_fac": "23/02/2026", "can_cre": 10, "p_cre": 44000, "can_cua": 20, "kg_cua": 792.4, "p_cua": 12000, "peso_man": 0, "p_man": 0, "desc": 450000, "flete": 0, "cond": "Gustavo Medell", "taj": 0},
        {"ruta": "MEDELLIN", "cliente": "Carlos Manizal", "f_emb": "22/02/2026", "f_fac": "23/02/2026", "can_cre": 38, "p_cre": 45000, "can_cua": 3, "kg_cua": 116.7, "p_cua": 12000, "peso_man": 4, "p_man": 16500, "desc": 690000, "flete": 0, "cond": "Gustavo Medell", "taj": 0},
        {"ruta": "MEDELLIN", "cliente": "Reinel Abuelo Medell", "f_emb": "22/02/2026", "f_fac": "23/02/2026", "can_cre": 6, "p_cre": 45500, "can_cua": 0, "kg_cua": 0, "p_cua": 0, "peso_man": 60, "p_man": 17000, "desc": 0, "flete": 0, "cond": "Gustavo Medell", "taj": 0},
        {"ruta": "MEDELLIN", "cliente": "David Pereira Medell", "f_emb": "22/02/2026", "f_fac": "23/02/2026", "can_cre": 9, "p_cre": 45000, "can_cua": 27, "kg_cua": 1096.9, "p_cua": 12300, "peso_man": 0, "p_man": 0, "desc": 0, "flete": 0, "cond": "Gustavo Medell", "taj": 0},
        {"ruta": "MEDELLIN", "cliente": "Daniel Taquera", "f_emb": "22/02/2026", "f_fac": "23/02/2026", "can_cre": 5, "p_cre": 46000, "can_cua": 0, "kg_cua": 0, "p_cua": 0, "peso_man": 0, "p_man": 0, "desc": 0, "flete": 0, "cond": "Gustavo Medell", "taj": 0},
    ]

    try:
        with transaction.atomic():
            tipo_can = TipoEmbalaje.objects.get_or_create(nombre='Canastilla')[0]
            summaries = []
            
            for r in insumo:
                ruta, _ = Ruta.objects.get_or_create(nombre=r["ruta"])
                
                # Cliente logic
                name_parts = r["cliente"].split(' ', 1)
                nombre = name_parts[0]
                apellido = name_parts[1] if len(name_parts) > 1 else ""
                
                # Unique ID consistent with previous import
                ident = f"NIT-{abs(hash(r['cliente'])) % 1000000}"
                cliente, created = Cliente.objects.get_or_create(
                    nombre=nombre, 
                    apellido=apellido,
                    defaults={
                        'numero_identificacion': ident,
                        'email': f"{ident}@erp.com",
                        'tipo_persona': 'natural',
                        'forma_pago': 'credito_15',
                        'ciudad': r["ruta"]
                    }
                )

                f_emb = datetime.strptime(r["f_emb"], "%d/%m/%Y").date()
                f_fac = datetime.strptime(r["f_fac"], "%d/%m/%Y").date()

                # Get or create shipment
                embarque, _ = Embarque.objects.get_or_create(
                    ruta=ruta,
                    fecha=f_emb,
                    conductor=r["cond"],
                    defaults={'estado': 'transito'}
                )
                if embarque.estado == 'borrador':
                    embarque.estado = 'transito'
                    embarque.save()

                # Build Invoice
                venta = Venta.objects.create(
                    cliente=cliente,
                    fecha=f_fac,
                    embarque=embarque,
                    conductor=r["cond"],
                    flete=Decimal(str(r["flete"])),
                    descuentos=Decimal(str(r["desc"])),
                    estado='DEBE'
                )

                items_added = []
                # 1. Crema (Units = Can * 16)
                if r["can_cre"] > 0:
                    units = r["can_cre"] * 16
                    emb_item, _ = EmbarqueItem.objects.get_or_create(
                        embarque=embarque, producto=p_crema,
                        defaults={'cantidad_unidades': 0, 'cantidad_kg': 0, 'tipo_embalaje': tipo_can}
                    )
                    emb_item.cantidad_unidades += Decimal(str(units))
                    emb_item.cantidad_disponible_unidades += Decimal(str(units))
                    emb_item.save()
                    
                    DetalleVenta.objects.create(
                        venta=venta, producto=p_crema, embarque_item=emb_item,
                        cantidad_unidades=Decimal(str(units)),
                        precio_unitario=Decimal(str(r["p_cre"])),
                        embalajes_entregados=Decimal(str(r["can_cre"]))
                    )
                    items_added.append(f"Crema ({units}u)")

                # 2. Cuajada (KG)
                if r["kg_cua"] > 0:
                    emb_item, _ = EmbarqueItem.objects.get_or_create(
                        embarque=embarque, producto=p_cuajada,
                        defaults={'cantidad_unidades': 0, 'cantidad_kg': 0, 'tipo_embalaje': tipo_can}
                    )
                    emb_item.cantidad_kg += Decimal(str(r["kg_cua"]))
                    emb_item.cantidad_disponible_kg += Decimal(str(r["kg_cua"]))
                    emb_item.cantidad_unidades += Decimal(str(r["can_cua"]))
                    emb_item.cantidad_disponible_unidades += Decimal(str(r["can_cua"]))
                    emb_item.save()

                    # Tajado logic (If we had a global tajado, we'd apply it here)
                    taj_bool = r["taj"] > 0
                    p_taj_und = Decimal('0')
                    if taj_bool:
                        p_taj_und = Decimal(str(r["taj"])) / Decimal(str(r["can_cua"] if r["can_cua"] > 0 else 1))

                    DetalleVenta.objects.create(
                        venta=venta, producto=p_cuajada, embarque_item=emb_item,
                        cantidad_kg=Decimal(str(r["kg_cua"])),
                        cantidad_unidades=Decimal(str(r["can_cua"])),
                        precio_unitario=Decimal(str(r["p_cua"])),
                        tajado=taj_bool,
                        precio_tajado_unidad=p_taj_und,
                        embalajes_entregados=Decimal(str(r["can_cua"]))
                    )
                    items_added.append(f"Cuajada ({r['kg_cua']}kg)")

                # 3. Mantequilla (KG)
                if r["peso_man"] > 0:
                    emb_item, _ = EmbarqueItem.objects.get_or_create(
                        embarque=embarque, producto=p_mantequilla,
                        defaults={'cantidad_unidades': 0, 'cantidad_kg': 0, 'tipo_embalaje': tipo_can}
                    )
                    emb_item.cantidad_kg += Decimal(str(r["peso_man"]))
                    emb_item.cantidad_disponible_kg += Decimal(str(r["peso_man"]))
                    emb_item.save()

                    DetalleVenta.objects.create(
                        venta=venta, producto=p_mantequilla, embarque_item=emb_item,
                        cantidad_kg=Decimal(str(r["peso_man"])),
                        precio_unitario=Decimal(str(r["p_man"]))
                    )
                    items_added.append(f"Mantequilla ({r['peso_man']}kg)")

                venta.actualizar_totales()
                summaries.append({
                    "fv": venta.factura,
                    "cli": r["cliente"],
                    "total": f"${venta.total_con_flete:,.2f}",
                    "items": ", ".join(items_added)
                })

            # Re-liquidate all Medellin shipments involved
            for emb_key in set([(r["ruta"], r["f_emb"], r["cond"]) for r in insumo]):
                ruta_obj = Ruta.objects.get(nombre=emb_key[0])
                f_obj = datetime.strptime(emb_key[1], "%d/%m/%Y").date()
                emb = Embarque.objects.get(ruta=ruta_obj, fecha=f_obj, conductor=emb_key[2])
                emb.calcular_resultados()

            print("\nRESULTADOS DE IMPORTACIÓN:")
            print("| FACTURA | CLIENTE | ITEMS | TOTAL |")
            print("| :--- | :--- | :--- | :--- |")
            for s in summaries:
                print(f"| {s['fv']} | {s['cli']} | {s['items']} | {s['total']} |")

    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        raise e

if __name__ == "__main__":
    run()
