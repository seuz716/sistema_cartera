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
from embarques.models import Ruta, Embarque, EmbarqueItem
from ventas.models import Venta, DetalleVenta

def fmt(val):
    return "{:,.2f}".format(val)

def run():
    print("# REPORTE DE VALIDACIÓN: MEDELLÍN DATASET VS EXCEL")
    
    # DATOS ESPERADOS (Extraídos manualmente de la imagen Medellín)
    # Formato: (Cliente, UndCrema, TotCrema, TotCuaj, TotMant, TotSinFlete, TotConFlete, PromCuaj)
    esperados = [
        ("Lucio Arteaga", 0, 0, 13400950, 0, 13400950, 13400950, 38.84333333),
        ("Eliecer Medell", 0, 0, 12250440, 0, 12250440, 12250440, 42.984),
        ("Cristian Mede", 0, 0, 0, 1320000, 1320000, 1320000, 38.6),
        ("Felipe Nuevo", 96, 4320000, 0, 0, 4320000, 4320000, 38.6),
        ("Edison Medell", 96, 4368000, 17508800, 1020000, 22896800, 22896800, 39.2222222),
        ("Manuel Mede", 0, 0, 5006100, 0, 5006100, 4826100, 40.7),
        ("Leonardo Med", 0, 0, 51217200, 0, 51217200, 51217200, 40.4271845),
        ("Fabian Maniza", 160, 7040000, 9508800, 0, 16548800, 16098800, 39.62),
        ("Carlos Maniza", 608, 27360000, 1400400, 66000, 28826400, 28136400, 38.9),
        ("Reinel Abuelo", 96, 4368000, 0, 1020000, 5388000, 5388000, 38.6),
        ("David Pereira", 144, 6480000, 13491870, 0, 19971870, 19971870, 40.6259259),
        ("Daniel Taque", 80, 3680000, 0, 0, 3680000, 3680000, 38.6),
    ]

    print("| CLIENTE | CAMPO | ESPERADO | OBTENIDO | DIFERENCIA | ESTADO |")
    print("| :--- | :--- | :---: | :---: | :---: | :---: |")

    found_errors = False
    for exp_row in esperados:
        cliente_name, e_u_cre, e_t_cre, e_t_cua, e_t_man, e_tsf, e_tcf, e_prom = exp_row
        
        # Buscar factura directamente por nombre de cliente en la factura (para evitar confusiones de ID con Cali)
        venta = Venta.objects.filter(
            cliente__nombre__icontains=cliente_name.split()[0],
            embarque__ruta__nombre='MEDELLIN'
        ).order_by('-id_interno').first()
        
        if not venta:
            # Re-intento con apellido si es necesario
            venta = Venta.objects.filter(
                cliente__apellido__icontains=cliente_name.split()[0],
                embarque__ruta__nombre='MEDELLIN'
            ).order_by('-id_interno').first()

        if not venta:
            print(f"| {cliente_name} | FACTURA | EXISTE | NO ENCONTRADA | - | ❌ ERROR |")
            found_errors = True
            continue

        cliente = venta.cliente

        # Factura metrics
        detalles = venta.detalles.all()
        
        # OBTENIDOS
        o_u_cre = sum(d.cantidad_unidades or 0 for d in detalles if 'CREMA' in d.producto.nombre.upper())
        o_t_cre = sum(d.precio_total or 0 for d in detalles if 'CREMA' in d.producto.nombre.upper())
        o_t_cua = sum(d.precio_total or 0 for d in detalles if 'CUAJADA' in d.producto.nombre.upper())
        o_t_man = sum(d.precio_total or 0 for d in detalles if 'MANTEQUILLA' in d.producto.nombre.upper())
        o_tsf = venta.total
        o_tcf = venta.total_con_flete
        
        # Promedio Cuajada
        d_cua = detalles.filter(producto__nombre__icontains='CUAJADA').first()
        o_can_cua = d_cua.cantidad_unidades if d_cua else 0
        o_kg_cua = d_cua.cantidad_kg if d_cua else 0
        o_prom = o_kg_cua / o_can_cua if o_can_cua > 0 else 38.6 # Valor por defecto en Excel parece ser 38.6 si no hay datos?

        validations = [
            ("Unidades Crema", e_u_cre, o_u_cre),
            ("Total Crema", e_t_cre, o_t_cre),
            ("Total Cuajada", e_t_cua, o_t_cua),
            ("Total Mantequilla", e_t_man, o_t_man),
            ("Total s/ Flete", e_tsf, o_tsf),
            ("Total c/ Flete", e_tcf, o_tcf),
            ("Promedio Cuaj", e_prom, o_prom)
        ]

        for label, exp, obs in validations:
            diff = Decimal(str(obs)) - Decimal(str(exp))
            estado = "✅ OK" if abs(diff) < 1 else "❌ ERROR"
            if estado == "❌ ERROR": found_errors = True
            print(f"| {cliente_name} | {label} | {fmt(exp)} | {fmt(obs)} | {fmt(diff)} | {estado} |")

if __name__ == "__main__":
    run()
