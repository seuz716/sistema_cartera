import os
import django
from decimal import Decimal
from datetime import datetime

# Setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from productos.models import Producto
from embarques.models import Ruta, Transportador, Vehiculo, Embarque, EmbarqueItem
from ventas.models import Venta, DetalleVenta
from clientes.models import Cliente
from django.contrib.auth.models import User

def get_or_create_products():
    crema, _ = Producto.objects.update_or_create(nombre='CREMA', defaults={'tipo_medida': 'unidad', 'control_inventario': True, 'precio_unitario': 45000})
    cuajada, _ = Producto.objects.update_or_create(nombre='CUAJADA', defaults={'tipo_medida': 'kg', 'control_inventario': True, 'precio_unitario': 12000, 'controla_peso_variable': True})
    mantequilla, _ = Producto.objects.update_or_create(nombre='MANTEQUILLA', defaults={'tipo_medida': 'kg', 'control_inventario': True, 'precio_unitario': 16500})
    tajado, _ = Producto.objects.update_or_create(nombre='TAJADO', defaults={'tipo_medida': 'unidad', 'control_inventario': False, 'precio_unitario': 0})
    return crema, cuajada, mantequilla, tajado

def process():
    crema, cuajada, mantequilla, tajado = get_or_create_products()
    admin_user = User.objects.filter(is_superuser=True).first()
    
    data = [
        {"cliente": "Lucio Arteaga Pop", "fecha_emb": "25/02/2026", "fecha_fac": "27/02/2026", "c_crema": 0, "p_crema": 0, "c_cuaj": 30, "kg_cuaj": 1165.3, "p_cuaj": 11500, "kg_mant": 0, "p_mant": 0, "desc": 0, "flete": 0, "driver": "Edinson Cali", "tajado": 0},
        {"cliente": "Eliecer Medellin", "fecha_emb": "22/02/2026", "fecha_fac": "24/02/2026", "c_crema": 0, "p_crema": 0, "c_cuaj": 25, "kg_cuaj": 1074.6, "p_cuaj": 11400, "kg_mant": 0, "p_mant": 0, "desc": 0, "flete": 0, "driver": "Gustavo Medellin", "tajado": 0},
        {"cliente": "Cristian Medellin", "fecha_emb": "22/02/2026", "fecha_fac": "24/02/2026", "c_crema": 0, "p_crema": 0, "c_cuaj": 0, "kg_cuaj": 0, "p_cuaj": 0, "kg_mant": 80, "p_mant": 16500, "desc": 0, "flete": 0, "driver": "Gustavo Medellin", "tajado": 0},
        {"cliente": "Felipe Nuevo", "fecha_emb": "22/02/2026", "fecha_fac": "24/02/2026", "c_crema": 6, "p_crema": 45000, "c_cuaj": 0, "kg_cuaj": 0, "p_cuaj": 0, "kg_mant": 0, "p_mant": 0, "desc": 0, "flete": 0, "driver": "Gustavo Medellin", "tajado": 0},
        {"cliente": "Edison Medellin", "fecha_emb": "22/02/2026", "fecha_fac": "24/02/2026", "c_crema": 6, "p_crema": 45500, "c_cuaj": 36, "kg_cuaj": 1412, "p_cuaj": 12400, "kg_mant": 60, "p_mant": 17000, "desc": 0, "flete": 0, "driver": "Gustavo Medellin", "tajado": 0},
        {"cliente": "Manuel Medellin", "fecha_emb": "22/02/2026", "fecha_fac": "24/02/2026", "c_crema": 0, "p_crema": 0, "c_cuaj": 10, "kg_cuaj": 407, "p_cuaj": 12300, "kg_mant": 0, "p_mant": 0, "desc": 180000, "flete": 0, "driver": "Gustavo Medellin", "tajado": 0},
        {"cliente": "Leonardo Medellin", "fecha_emb": "22/02/2026", "fecha_fac": "23/02/2026", "c_crema": 0, "p_crema": 0, "c_cuaj": 103, "kg_cuaj": 4164, "p_cuaj": 12300, "kg_mant": 0, "p_mant": 0, "desc": 0, "flete": 0, "driver": "Gustavo Medellin", "tajado": 0},
        {"cliente": "Fabian Manizales", "fecha_emb": "22/02/2026", "fecha_fac": "23/02/2026", "c_crema": 10, "p_crema": 44000, "c_cuaj": 20, "kg_cuaj": 792.4, "p_cuaj": 12000, "kg_mant": 0, "p_mant": 0, "desc": 450000, "flete": 0, "driver": "Gustavo Medellin", "tajado": 0},
        {"cliente": "Carlos Manizales", "fecha_emb": "22/02/2026", "fecha_fac": "23/02/2026", "c_crema": 38, "p_crema": 45000, "c_cuaj": 3, "kg_cuaj": 116.7, "p_cuaj": 12000, "kg_mant": 4, "p_mant": 16500, "desc": 690000, "flete": 0, "driver": "Gustavo Medellin", "tajado": 0},
        {"cliente": "Reinel Abuelo Per", "fecha_emb": "22/02/2026", "fecha_fac": "23/02/2026", "c_crema": 6, "p_crema": 45500, "c_cuaj": 0, "kg_cuaj": 0, "p_cuaj": 0, "kg_mant": 60, "p_mant": 17000, "desc": 0, "flete": 0, "driver": "Gustavo Medellin", "tajado": 0},
        {"cliente": "David Pereira", "fecha_emb": "22/02/2026", "fecha_fac": "23/02/2026", "c_crema": 9, "p_crema": 45000, "c_cuaj": 27, "kg_cuaj": 1096.9, "p_cuaj": 12300, "kg_mant": 0, "p_mant": 0, "desc": 0, "flete": 0, "driver": "Gustavo Medellin", "tajado": 0},
        {"cliente": "Daniel Taquez Cend", "fecha_emb": "22/02/2026", "fecha_fac": "23/02/2026", "c_crema": 5, "p_crema": 46000, "c_cuaj": 0, "kg_cuaj": 0, "p_cuaj": 0, "kg_mant": 0, "p_mant": 0, "desc": 0, "flete": 0, "driver": "Gustavo Medellin", "tajado": 0},
    ]
    
    with transaction.atomic():
        ruta_med, _ = Ruta.objects.get_or_create(nombre='MEDELLIN')
        
        # Group by embarque
        shipments_data = {}
        for row in data:
            key = (row['fecha_emb'], row['driver'])
            if key not in shipments_data:
                shipments_data[key] = []
            shipments_data[key].append(row)
            
        summary = []
        
        for (f_emb_str, driver_name), rows in shipments_data.items():
            f_emb = datetime.strptime(f_emb_str, "%d/%m/%Y").date()
            trans, _ = Transportador.objects.get_or_create(
                nombre=driver_name, 
                defaults={'documento': driver_name.replace(" ", "")[:20]}
            )
            
            veh, _ = Vehiculo.objects.get_or_create(
                placa=f"MED-{driver_name[:3].upper()}", 
                defaults={'capacidad_carga_kg': 15000}
            )
            
            emb = Embarque.objects.create(
                fecha=f_emb,
                ruta=ruta_med,
                transportador=trans,
                vehiculo=veh,
                conductor=driver_name,
                estado='transito',
                usuario_registro=admin_user
            )
            
            emb_items_calc = {crema.id: 0, cuajada.id: 0, mantequilla.id: 0}
            
            for row in rows:
                cli_name = row['cliente']
                cli, _ = Cliente.objects.get_or_create(
                    nombre=cli_name,
                    defaults={
                        'numero_identificacion': cli_name.replace(" ", "")[:20],
                        'apellido': 'CARGA_MASIVA',
                        'email': f"{cli_name.replace(' ', '').lower()}@excel.com",
                        'telefono': '0000000',
                        'direccion': 'Dirección Conocida'
                    }
                )
                
                f_fac = datetime.strptime(row['fecha_fac'], "%d/%m/%Y").date()
                venta = Venta.objects.create(
                    cliente=cli,
                    embarque=emb,
                    fecha=f_fac,
                    flete=Decimal(str(row['flete'])),
                    descuentos=Decimal(str(row['desc'])),
                    estado='DEBE',
                    usuario_registro=admin_user
                )
                
                # Crema
                if row['c_crema'] > 0:
                    units = row['c_crema'] * 16
                    DetalleVenta.objects.create(
                        venta=venta, producto=crema, 
                        cantidad_unidades=units, 
                        precio_unitario=Decimal(str(row['p_crema'])),
                        embalajes_entregados=row['c_crema']
                    )
                    emb_items_calc[crema.id] += units
                
                # Cuajada
                if row['kg_cuaj'] > 0:
                    DetalleVenta.objects.create(
                        venta=venta, producto=cuajada, 
                        cantidad_kg=Decimal(str(row['kg_cuaj'])), 
                        precio_unitario=Decimal(str(row['p_cuaj'])),
                        embalajes_entregados=row['c_cuaj']
                    )
                    emb_items_calc[cuajada.id] += Decimal(str(row['kg_cuaj']))
                
                # Mantequilla
                if row['kg_mant'] > 0:
                    DetalleVenta.objects.create(
                        venta=venta, producto=mantequilla, 
                        cantidad_kg=Decimal(str(row['kg_mant'])), 
                        precio_unitario=Decimal(str(row['p_mant']))
                    )
                    emb_items_calc[mantequilla.id] += Decimal(str(row['kg_mant']))
                
                # Tajado
                if row['tajado'] > 0:
                    DetalleVenta.objects.create(
                        venta=venta, producto=tajado, 
                        cantidad_unidades=1, 
                        precio_unitario=Decimal(str(row['tajado']))
                    )
                
                venta.actualizar_totales()
                venta.refresh_from_db()
                summary.append({
                    "id": venta.factura,
                    "cliente": cli.nombre,
                    "total": venta.total_con_flete
                })
            
            # Load the truck with exactly what was sold (since it's historical data)
            for prod_id, total_qty in emb_items_calc.items():
                if total_qty > 0:
                    p = Producto.objects.get(id=prod_id)
                    item = EmbarqueItem.objects.create(
                        embarque=emb,
                        producto=p,
                        cantidad_unidades=total_qty if p.tipo_medida == 'unidad' else 0,
                        cantidad_kg=total_qty if p.tipo_medida == 'kg' else 0,
                        cantidad_disponible_unidades=0,
                        cantidad_disponible_kg=0
                    )
            
            emb.calcular_resultados()
            print(f"Embarque {emb.numero} procesado.")
            
        return summary

if __name__ == "__main__":
    results = process()
    print("\nRESUMEN DE PROCESAMIENTO:")
    for r in results:
        print(f"Factura: {r['id']} | Cliente: {r['cliente']} | Total: ${r['total']:,.2f}")
