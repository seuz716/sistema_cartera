import os
import django
from decimal import Decimal

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from productos.models import Producto
from embarques.models import Embarque, EmbarqueItem, Ruta, Transportador, Vehiculo, CapacidadEmbalaje
from ventas.models import Venta, DetalleVenta
from clientes.models import Cliente
from django.db import transaction

def qa_audit_report():
    print("Iniciando Proceso de Validación Transaccional (Escenario MEDELLÍN)")
    
    with transaction.atomic():
        # 1. Setup Master Data
        # Products
        crema, _ = Producto.objects.get_or_create(nombre='CREMA EXCEL', tipo_medida='unidad', defaults={'precio_unitario': 45000})
        cuajada, _ = Producto.objects.get_or_create(nombre='CUAJADA EXCEL', tipo_medida='kg', defaults={'precio_unitario': 11500})
        mantequilla, _ = Producto.objects.get_or_create(nombre='MANTEQUILLA EXCEL', tipo_medida='unidad', defaults={'precio_unitario': 16500})
        tajado, _ = Producto.objects.get_or_create(nombre='TAJADO EXCEL', tipo_medida='unidad', defaults={'control_inventario': False})

        # Capacidad Crema (16 units per basket)
        CapacidadEmbalaje.objects.update_or_create(producto=crema, defaults={'unidades_por_paquete': 16})
        
        # Infra
        ruta, _ = Ruta.objects.get_or_create(nombre='MEDELLIN')
        tra, _ = Transportador.objects.get_or_create(nombre='Gustavo Medellin')
        veh, _ = Vehiculo.objects.get_or_create(placa='MED-123')
        
        # Embarque (Large stock to allow all sales)
        emb = Embarque.objects.create(ruta=ruta, transportador=tra, vehiculo=veh, estado='transito')
        EmbarqueItem.objects.create(embarque=emb, producto=crema, cantidad_unidades=5000, cantidad_disponible_unidades=5000)
        EmbarqueItem.objects.create(embarque=emb, producto=cuajada, cantidad_kg=10000, cantidad_disponible_kg=10000)
        EmbarqueItem.objects.create(embarque=emb, producto=mantequilla, cantidad_unidades=5000, cantidad_disponible_unidades=5000)

        # 2. Excel Data Matrix (Medellin Rows)
        # Row format: (Cliente, canast_crema, p_crema, canast_cuaj, kg_cuaj, p_cuaj, und_mant, p_mant, flete, tajado_val, expected_total_sin_flete, expected_total_con_flete, expected_avg_kg)
        medellin_data = [
            ("Lucio Arteaga Pop", 0, 0, 30, 1165.3, 11500, 0, 0, 0, 0, 13400950, 13400950, 38.84333),
            ("Eliecer Medellin", 0, 0, 25, 1074.6, 11400, 0, 0, 0, 0, 12250440, 12250440, 42.984),
            ("Cristian Medellin", 0, 0, 0, 0, 0, 80, 16500, 0, 0, 1320000, 1320000, 0),
            ("Felipe Nuevo", 6, 45000, 0, 0, 0, 0, 0, 0, 0, 4320000, 4320000, 38.00),
            ("Edison Medellin", 6, 45500, 36, 1412, 12400, 60, 17000, 0, 0, 22896800, 22896800, 39.22222),
            ("Manuel Medellin", 0, 0, 10, 407, 12300, 0, 0, 180000, 0, 5006100, 4826100, 40.7),
            ("Leonardo Medellin", 0, 0, 103, 4164, 12300, 0, 0, 0, 0, 51217200, 51217200, 40.42718),
            ("Fabian Manizales", 10, 44000, 20, 792.4, 12000, 0, 0, 450000, 0, 16548800, 16098800, 39.62),
            ("Carlos Manizales", 38, 45000, 3, 116.7, 12000, 4, 16500, 690000, 0, 28826400, 28136400, 38.9),
            ("Reinel Abuelo Per", 6, 45500, 0, 0, 0, 60, 17000, 0, 0, 5388000, 5388000, 38.60),
            ("David Pereira", 9, 45000, 27, 1096.9, 12300, 0, 0, 0, 0, 19971870, 19971870, 40.62592),
            ("Daniel Taquez Cend", 5, 46000, 0, 0, 0, 0, 0, 0, 0, 3680000, 3680000, 38.00)
        ]

        report = []
        fmt_header = "{:<20} | {:<15} | {:<15} | {:<15} | {:<12} | {:<8}"
        print(fmt_header.format("Cliente", "Campo", "Esperado", "Obtenido", "Diferencia", "Estado"))
        print("-" * 100)

        for row in medellin_data:
            name, c_crema, p_crema, c_cuaj, kg_cuaj, p_cuaj, u_mant, p_mant, flete, taj, exp_sin, exp_con, exp_avg = row
            cli, _ = Cliente.objects.get_or_create(nombre=name, defaults={'numero_identificacion': '999'+name[:3]})
            
            # Create Venta
            v = Venta.objects.create(cliente=cli, embarque=emb, fecha=emb.fecha, flete=Decimal(str(flete)))
            
            # Items
            if c_crema > 0:
                DetalleVenta.objects.create(
                    venta=v, producto=crema, embalajes_entregados=c_crema, 
                    precio_unitario=Decimal(str(p_crema))
                )
            if kg_cuaj > 0:
                DetalleVenta.objects.create(
                    venta=v, producto=cuajada, cantidad_kg=Decimal(str(kg_cuaj)), 
                    precio_unitario=Decimal(str(p_cuaj)), embalajes_entregados=c_cuaj
                )
            if u_mant > 0:
                DetalleVenta.objects.create(
                    venta=v, producto=mantequilla, cantidad_unidades=Decimal(str(u_mant)), 
                    precio_unitario=Decimal(str(p_mant))
                )
            if taj > 0:
                 DetalleVenta.objects.create(
                    venta=v, producto=tajado, cantidad_unidades=1, 
                    precio_unitario=Decimal(str(taj))
                )

            v.actualizar_totales()
            v.refresh_from_db()
            
            # Checks
            checks = [
                ("Total Sin Flete", Decimal(str(exp_sin)), v.total),
                ("Total Con Flete", Decimal(str(exp_con)), v.total_con_flete),
            ]
            
            # Verification Crema Units
            if c_crema > 0:
                det = v.detalles.get(producto=crema)
                checks.append(("Und Crema", Decimal(str(c_crema * 16)), det.cantidad_unidades))
            
            # Averaging check (Manual check in loop)
            if c_cuaj > 0:
                avg = float(kg_cuaj) / float(c_cuaj)
                # This check is more for documentation as system doesn't store "avg" but we can check if it matches row.
                checks.append(("Avg Kg Cuaj", Decimal(str(round(exp_avg, 5))), Decimal(str(round(avg, 5)))))

            for label, expected, obtained in checks:
                diff = obtained - expected
                status = "OK" if abs(diff) < 0.01 else "ERROR"
                print(fmt_header.format(name[:20], label, f"{expected:,.2f}", f"{obtained:,.2f}", f"{diff:,.2f}", status))

        raise Exception("Rollback intentional to keep DB clean during audit")

if __name__ == "__main__":
    try:
        qa_audit_report()
    except Exception as e:
        if str(e) != "Rollback intentional to keep DB clean during audit":
            print(f"Error fatal: {e}")
        else:
            print("\nAuditoría finalizada. Los datos mostrados arriba son basados en el motor transaccional.")
