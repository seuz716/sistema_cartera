from decimal import Decimal

def run():
    # DATOS CALCULADOS PREVIAMENTE (Obtenidos del paso anterior)
    obtenidos = [
        {"cliente": "Andres Bordo", "unds_crema": 48, "p_crema": 2160000, "p_cuaj": 3895410, "total_sin_flete": 5271411, "total_final": 5271411, "prom_cuaj": 39.59},
        {"cliente": "Claudia Reine", "unds_crema": 32, "p_crema": 1440000, "p_cuaj": 0, "total_sin_flete": 1440000, "total_final": 1440000, "prom_cuaj": 0.00},
        {"cliente": "Lacteos alian", "unds_crema": 288, "p_crema": 12960000, "p_cuaj": 0, "total_sin_flete": 12780000, "total_final": 12780000, "prom_cuaj": 0.00},
        {"cliente": "Nelson Carta", "unds_crema": 96, "p_crema": 4320000, "p_cuaj": 2797200, "total_sin_flete": 7117200, "total_final": 7117200, "prom_cuaj": 38.85},
        {"cliente": "Silvio Pereira", "unds_crema": 160, "p_crema": 7200000, "p_cuaj": 5614800, "total_sin_flete": 239725, "total_final": 239725, "prom_cuaj": 38.99},
        {"cliente": "Reinel Abuelo", "unds_crema": 80, "p_crema": 3600000, "p_cuaj": 2711700, "total_sin_flete": 6086700, "total_final": 6086700, "prom_cuaj": 39.30},
        {"cliente": "Alexander La", "unds_crema": 48, "p_crema": 2112000, "p_cuaj": 14057600, "total_sin_flete": 16169600, "total_final": 16169600, "prom_cuaj": 38.20},
        {"cliente": "David Pereira", "unds_crema": 80, "p_crema": 3600000, "p_cuaj": 7981200, "total_sin_flete": 8786600, "total_final": 8786600, "prom_cuaj": 39.12},
        {"cliente": "Martha Boliva", "unds_crema": 0, "p_crema": 0, "p_cuaj": 8866000, "total_sin_flete": 8866000, "total_final": 8866000, "prom_cuaj": 40.30},
    ]

    # DATOS ESPERADOS (Extraídos de la imagen)
    # Basados en las columnas a la derecha de la imagen: unds crema, precio total crema, precio total cuajada, precio total mantequilla, Total factura sin flete, Total flete descontado, Kg cuajada promedio
    # Nota: Los campos #N/D en la imagen se tratan como errores de Excel o valores no definidos por el usuario en el insumo.
    esperados = [
        {"cliente": "Andres Bordo", "unds_crema": 48, "p_crema": 2160000, "p_cuaj": 3895410, "total_sin_flete": None, "total_final": None, "prom_cuaj": 39.5875},
        {"cliente": "Claudia Reine", "unds_crema": 32, "p_crema": 1440000, "p_cuaj": 0, "total_sin_flete": None, "total_final": None, "prom_cuaj": 38.6}, # Nota: La imagen dice 38.6 pero Claudia no tiene canastillas cuajada en el insumo original. El Excel parece tener una fórmula arrastrada.
        {"cliente": "Lacteos alian", "unds_crema": 288, "p_crema": 12960000, "p_cuaj": 0, "total_sin_flete": None, "total_final": None, "prom_cuaj": 38.6}, 
        {"cliente": "Nelson Carta", "unds_crema": 96, "p_crema": 4320000, "p_cuaj": 2797200, "total_sin_flete": None, "total_final": None, "prom_cuaj": 38.85},
        {"cliente": "Silvio Pereira", "unds_crema": 160, "p_crema": 7200000, "p_cuaj": 5614800, "total_sin_flete": None, "total_final": None, "prom_cuaj": 38.9916667},
        {"cliente": "Reinel Abuelo", "unds_crema": 80, "p_crema": 3600000, "p_cuaj": 2711700, "total_sin_flete": None, "total_final": None, "prom_cuaj": 39.3},
        {"cliente": "Alexander La", "unds_crema": 48, "p_crema": 2112000, "p_cuaj": 14057600, "total_sin_flete": None, "total_final": None, "prom_cuaj": 38.2},
        {"cliente": "David Pereira", "unds_crema": 80, "p_crema": 3600000, "p_cuaj": 7981200, "total_sin_flete": None, "total_final": None, "prom_cuaj": 39.1235294},
        {"cliente": "Martha Boliva", "unds_crema": 0, "p_crema": 0, "p_cuaj": 8866000, "total_sin_flete": None, "total_final": None, "prom_cuaj": 40.3},
    ]

    print("# REPORTE DE COMPARACIÓN TÉCNICA (AUDITORÍA VS EXCEL)")
    print("| CLIENTE | CAMPO | ESPERADO (EXCEL) | OBTENIDO (SISTEMA) | ESTADO | DIFERENCIA |")
    print("| :--- | :--- | :---: | :---: | :---: | :---: |")

    for i in range(len(obtenidos)):
        cli = obtenidos[i]["cliente"]
        obs = obtenidos[i]
        esp = esperados[i]

        campos = [
            ("Unidades Crema", "unds_crema"),
            ("Precio Total Crema", "p_crema"),
            ("Precio Total Cuajada", "p_cuaj"),
            ("Promedio Cuaj/Can", "prom_cuaj"),
            ("Total Sin Flete", "total_sin_flete"),
            ("Total Flete Descontado", "total_final")
        ]

        for label, key in campos:
            val_esp = esp.get(key)
            val_obs = obs.get(key)
            
            if val_esp is None:
                estado = "⚠️ #N/D"
                dif = "N/A"
            else:
                d = Decimal(str(val_obs)) - Decimal(str(val_esp))
                if abs(d) < 0.01:
                    estado = "✅ OK"
                    dif = "0"
                else:
                    estado = "❌ ERROR"
                    dif = "{:,.4f}".format(d)
            
            print(f"| {cli} | {label} | {val_esp if val_esp is not None else '#N/D'} | {val_obs} | {estado} | {dif} |")

if __name__ == "__main__":
    run()
