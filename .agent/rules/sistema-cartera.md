# Reglas del Proyecto: Sistema Cartera

Como asistente de IA, debes seguir estas reglas estrictamente para mantener la integridad del sistema.

## 🛡️ Seguridad
1. **Nunca hardcodear claves**: Todas las API Keys, Secret Keys o credenciales deben ir en el archivo `.env`.
2. **Autenticación**: Todas las vistas (FBV o CBV) deben estar protegidas. Usa `@login_required` para funciones y `LoginRequiredMixin` para clases.
3. **CSRF**: No usar `csrf_exempt` a menos que sea estrictamente necesario para integraciones externas seguras.
4. **Variables de Entorno**: Actualizar siempre `.env.example` cuando se agregue una nueva variable.

## 🐍 Convenciones de Código
1. **Nombres**: Usar `snake_case` para variables y funciones, `PascalCase` para clases (modelos, vistas, formularios).
2. **Idioma**: Código y comentarios técnicos en inglés son aceptables, pero los mensajes al usuario final deben estar en **Español**.
3. **Documentación**: Cada función compleja debe tener un docstring explicando qué hace.

## 📊 Estándares de Modelos Django
1. **Cálculos Financieros**: Usar `DecimalField` para dinero. Nunca `FloatField`.
2. **Señales**: Usa señales (`signals.py`) para cálculos automáticos de saldos (ej: actualizar total de venta al guardar detalle).
3. **Agnosticismo**: No uses Raw SQL. Mantente fiel al ORM para permitir migración fácil a PostgreSQL.

## 📥 Importación de Datos
1. El script `importar_proveedores.py` es el estándar. Debe incluir:
   - Validación previa del CSV.
   - Limpieza de espacios en blanco.
   - Transacciones atómicas.
   - Reporte de filas procesadas/fallidas.
