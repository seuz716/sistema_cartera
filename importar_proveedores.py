import csv
import django
import os
import sys
from django.db import transaction

# Configuración de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from proveedores.models import Proveedor
from recoleccion.models import Ruta

def clean_row(row):
    """Limpia espacios en blanco y normaliza datos."""
    return {k.strip(): (v.strip() if v else "") for k, v in row.items()}

def validate_csv(file_path):
    """Valida el CSV antes de importar."""
    errors = []
    required_fields = ["identificacion", "nombre", "ruta"]
    seen_ids = set()
    
    with open(file_path, encoding="utf-8-sig", newline="") as file:
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(file.read(2048))
            file.seek(0)
            reader = csv.DictReader(file, dialect=dialect)
        except Exception as e:
            return False, [f"Error al leer el formato del CSV: {e}"]

        # Validar columnas
        actual_fields = [f.replace("ï»¿", "").strip() for f in reader.fieldnames]
        for field in required_fields:
            if field not in actual_fields:
                errors.append(f"Columna faltante: {field}")
        
        if errors:
            return False, errors

        for i, row in enumerate(reader, start=2):
            row = clean_row(row)
            ident = row.get("identificacion")
            if not ident:
                errors.append(f"Fila {i}: Identificación vacía")
            elif ident in seen_ids:
                errors.append(f"Fila {i}: Identificación duplicada en el archivo ({ident})")
            seen_ids.add(ident)

    return len(errors) == 0, errors

def import_data(file_path):
    stats = {"creados": 0, "actualizados": 0, "errores": 0}
    
    with open(file_path, encoding="utf-8-sig", newline="") as file:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(file.read(2048))
        file.seek(0)
        reader = csv.DictReader(file, dialect=dialect)
        
        # Normalizar claves
        reader.fieldnames = [f.replace("ï»¿", "").strip() for f in reader.fieldnames]

        for i, row in enumerate(reader, start=2):
            row = clean_row(row)
            try:
                with transaction.atomic():
                    ruta_nombre = row.get("ruta", "Sin Ruta")
                    ruta_obj, _ = Ruta.objects.get_or_create(nombre=ruta_nombre)

                    proveedor, created = Proveedor.objects.update_or_create(
                        identificacion=row["identificacion"],
                        defaults={
                            "nombre": row["nombre"],
                            "telefono": row.get("telefono"),
                            "email": row.get("email"),
                            "direccion": row.get("direccion"),
                            "ruta": ruta_obj,
                        }
                    )
                    
                    if created:
                        stats["creados"] += 1
                    else:
                        stats["actualizados"] += 1
                        
            except Exception as e:
                print(f"Error procesando fila {i} ({row.get('nombre')}): {e}")
                stats["errores"] += 1

    return stats

if __name__ == "__main__":
    csv_path = "proveedores.csv"
    if not os.path.exists(csv_path):
        print(f"Error: No se encuentra el archivo {csv_path}")
        sys.exit(1)

    print("--- Iniciando Validación ---")
    is_valid, messages = validate_csv(csv_path)
    if not is_valid:
        print("El archivo tiene errores y no puede ser procesado:")
        for msg in messages:
            print(f"- {msg}")
        sys.exit(1)
    
    print("Validación exitosa. Importando datos...")
    results = import_data(csv_path)
    
    print("\n--- Reporte de Importación ---")
    print(f"Proveedores Creados:    {results['creados']}")
    print(f"Proveedores Actualizados: {results['actualizados']}")
    print(f"Errores encontrados:    {results['errores']}")
    print("------------------------------")
