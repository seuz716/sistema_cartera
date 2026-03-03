from decimal import Decimal

def run():
    # DATOS CALCULADOS POR EL SISTEMA (Reglas del Auditor)
    obtenidos = [
        {"cliente": "Andres Bordo", "unds_crema": 48, "p_crema": 2160000, "p_cuaj": 3895410, "can_cuaj": 8, "kg_cuaj": 316.7, "total_sin_flete": 5271411, "total_final": 5271411},
        {"cliente": "Claudia Reine", "unds_crema": 32, "p_crema": 1440000, "p_cuaj": 0, "can_cuaj": 0, "kg_cuaj": 0, "total_sin_flete": 1440000, "total_final": 1440000},
        {"cliente": "Lacteos alian", "unds_crema": 288, "p_crema": 12960000, "p_cuaj": 0, "can_cuaj": 0, "kg_cuaj": 0, "total_sin_flete": 12780000, "total_final": 12780000},
        {"cliente": "Nelson Carta", "unds_crema": 96, "p_crema": 4320000, "p_cuaj": 2797200, "can_cuaj": 6, "kg_cuaj": 233.1, "total_sin_flete": 7117200, "total_final": 7117200},
        {"cliente": "Silvio Pereira", "unds_crema": 160, "p_crema": 7200000, "p_cuaj": 5614800, "can_cuaj": 12, "kg_cuaj": 467.9, "total_sin_flete": 239725, "total_final": 239725},
        {"cliente": "Reinel Abuelo", "unds_crema": 80, "p_crema": 3600000, "p_cuaj": 2711700, "can_cuaj": 6, "kg_cuaj": 235.8, "total_sin_flete": 6086700, "total_final": 6086700},
        {"cliente": "Alexander La", "unds_crema": 48, "p_crema": 2112000, "p_cuaj": 14057600, "can_cuaj": 32, "kg_cuaj": 1222.4, "total_sin_flete": 16169600, "total_final": 16169600},
        {"cliente": "David Pereira", "unds_crema": 80, "p_crema": 3600000, "p_cuaj": 7981200, "can_cuaj": 17, "kg_cuaj": 665.1, "total_sin_flete": 8786600, "total_final": 8786600},
        {"cliente": "Martha Boliva", "unds_crema": 0, "p_crema": 0, "p_cuaj": 8866000, "can_cuaj": 20, "kg_cuaj": 806.0, "total_sin_flete": 8866000, "total_final": 8866000},
        {"cliente": "Lucio Arteaga", "unds_crema": 0, "p_crema": 0, "p_cuaj": 13400950, "can_cuaj": 30, "kg_cuaj": 1165.3, "total_sin_flete": 13400950, "total_final": 13400950},
    ]

    # DATOS ESPERADOS (Excel)
    esperados = [
        {"cliente": "Andres Bordo", "unds_crema": 48, "p_crema": 2160000, "p_cuaj": 3895410, "prom_cuaj": 39.5875},
        {"cliente": "Claudia Reine", "unds_crema": 32, "p_crema": 1440000, "p_cuaj": 0, "prom_cuaj": None}, 
        {"cliente": "Lacteos alian", "unds_crema": 288, "p_crema": 12960000, "p_cuaj": 0, "prom_cuaj": None}, 
        {"cliente": "Nelson Carta", "unds_crema": 96, "p_crema": 4320000, "p_cuaj": 2797200, "prom_cuaj": 38.85},
        {"cliente": "Silvio Pereira", "unds_crema": 160, "p_crema": 7200000, "p_cuaj": 5614800, "prom_cuaj": 38.9916667},
        {"cliente": "Reinel Abuelo", "unds_crema": 80, "p_crema": 3600000, "p_cuaj": 2711700, "prom_cuaj": 39.3},
        {"cliente": "Alexander La", "unds_crema": 48, "p_crema": 2112000, "p_cuaj": 14057600, "prom_cuaj": 38.2},
        {"cliente": "David Pereira", "unds_crema": 80, "p_crema": 3600000, "p_cuaj": 7981200, "prom_cuaj": 39.1235294},
        {"cliente": "Martha Boliva", "unds_crema": 0, "p_crema": 0, "p_cuaj": 8866000, "prom_cuaj": 40.3},
        {"cliente": "Lucio Arteaga", "unds_crema": 0, "p_crema": 0, "p_cuaj": 13400950, "prom_cuaj": 38.8433333},
    ]

    print("# REPORTE DE CALIBRACIÓN DE PROMEDIOS (CUAJADA)")
    print("| CLIENTE | KG CUAJADA | CANASTILLAS | PROMEDIO OBTENIDO | ESPERADO (EXCEL) | ESTADO |")
    print("| :--- | :---: | :---: | :---: | :---: | :---: |")

    for obs in obtenidos:
        esp = next((e for e in esperados if e["cliente"] == obs["cliente"]), None)
        if not esp: continue
        
        kg = obs["kg_cuaj"]
        can = obs["can_cuaj"]
        val_esp = esp["prom_cuaj"]
        
        # Nueva lógica de promedio
        if can > 0:
            val_obs = kg / can
            obs_str = "{:,.4f}".format(val_obs)
            
            if val_esp is not None:
                d = abs(Decimal(str(val_obs)) - Decimal(str(val_esp)))
                estado = "✅ OK" if d < Decimal("0.01") else "❌ VARIA"
                esp_str = "{:,.4f}".format(val_esp)
            else:
                estado = "⚠️ EXCEL N/D"
                esp_str = "N/D"
        else:
            val_obs = "N/A"
            obs_str = "N/A"
            estado = "✅ OK" if val_esp is None else "❌ ERROR"
            esp_str = "N/D" if val_esp is None else "{:,.4f}".format(val_esp)

        print(f"| {obs['cliente']} | {kg} | {can} | {obs_str} | {esp_str} | {estado} |")

if __name__ == "__main__":
    run()
