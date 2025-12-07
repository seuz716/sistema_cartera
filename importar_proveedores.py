import csv
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from proveedores.models import Proveedor
from recoleccion.models import Ruta

with open("proveedores.csv", encoding="utf-8-sig", newline="") as file:
    # Detecta automáticamente si separa por , o ;
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(file.read(2048))
    file.seek(0)

    reader = csv.DictReader(file, dialect=dialect)

    # Normalizar claves (quitar BOM y espacios)
    fieldnames = [f.replace("ï»¿", "").strip() for f in reader.fieldnames]
    reader.fieldnames = fieldnames

    for row in reader:
        # Asegurar que NO hay espacios ni caracteres raros
        row = {k.strip(): (v.strip() if v else "") for k, v in row.items()}

        ruta_nombre = row["ruta"]
        ruta_obj, _ = Ruta.objects.get_or_create(nombre=ruta_nombre)

        Proveedor.objects.update_or_create(
            identificacion=row["identificacion"],
            defaults={
                "nombre": row["nombre"],
                "telefono": row["telefono"],
                "email": row["email"],
                "direccion": row["direccion"],
                "ruta": ruta_obj,
            }
        )

        print("Proveedor importado:", row["nombre"])
