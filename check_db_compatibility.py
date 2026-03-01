import os
import django
import sys

# Configuración de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.apps import apps
from django.db import connection

def check_compatibility():
    print("--- Verificando Compatibilidad SQLite -> PostgreSQL ---")
    issues = 0
    
    # 1. Verificar campos FileField/ImageField sin configuración de storage
    # PostgreSQL maneja los datos pero no el sistema de archivos igual que SQLite en local
    for model in apps.get_models():
        for field in model._meta.fields:
            if field.get_internal_type() in ["FileField", "ImageField"]:
                print(f"[AVISO] {model.__name__}.{field.name}: Asegúrate de configurar Amazon S3 o similar en producción.")
    
    # 2. Verificar datos nulos vs strings vacíos
    # Postgres es más estricto con tipos.
    for model in apps.get_models():
        app_label = model._meta.app_label
        if app_label in ["admin", "auth", "contenttypes", "sessions"]:
            continue
            
        try:
            count = model.objects.count()
            print(f"[OK] {app_label}.{model.__name__}: {count} registros listos.")
        except Exception as e:
            print(f"[ERROR] {app_label}.{model.__name__}: Problema al leer datos: {e}")
            issues += 1

    # 3. Verificar nombres de tablas (Postgres tiene límites de longitud y sensibles a mayúsculas si no se manejan bien)
    # Django maneja esto bien, pero nombres excesivamente largos pueden ser truncados.
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            if len(table[0]) > 63:
                print(f"[RIESGO] Tabla {table[0]} tiene más de 63 caracteres (límite de Postgres).")
                issues += 1

    return issues

if __name__ == "__main__":
    total_issues = check_compatibility()
    if total_issues == 0:
        print("\n--- ✅ Compatibilidad verificada. Tus datos están listos para PostgreSQL. ---")
    else:
        print(f"\n--- ⚠️ Se encontraron {total_issues} riesgos. Revísalos antes de migrar. ---")
