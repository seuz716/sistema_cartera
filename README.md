# Sistema de Gestión de Cartera y Logística

Este proyecto es una plataforma robusta para la gestión operativa de negocios de distribución, cobranza y logística, potenciada por Inteligencia Artificial (Google Gemini).

## 🚀 Requisitos
- **Python**: 3.10 o superior.
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción).
- **API Key**: Google Gemini API Key.

## 🛠️ Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <url-del-repositorio>
   cd sistema_cartera
   ```

2. **Crear entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Linux/Mac
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   Copia el archivo `.env.example` a `.env` y rellena los datos:
   ```bash
   cp .env.example .env
   ```

5. **Migrar base de datos**:
   ```bash
   python manage.py migrate
   ```

6. **Crear superusuario**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Iniciar servidor**:
   ```bash
   python manage.py runserver
   ```

## 🧠 Módulo de IA
El sistema utiliza Google Gemini para:
- **Análisis de Riesgo**: Evalúa el comportamiento de pago de los clientes.
- **Asistente de Chat**: Ayuda interna para consultas rápidas.
- **Control de Tokens**: Incluye un manager que limita el consumo diario para evitar costos inesperados.

## 📁 Estructura del Proyecto
- `clientes/`, `proveedores/`: Gestión de perfiles y crédito.
- `ventas/`, `cartera/`: Facturación, pagos y saldos incrementales.
- `embarques/`, `recoleccion/`: Logística de transporte y rutas.
- `modulo_ia/`: Integración con Gemini y Token Manager.
- `config/`: Ajustes centrales del proyecto.

## 🤝 Contribución
1. Sigue las reglas definidas en `.agent/rules/sistema-cartera.md`.
2. Asegúrate de que todas las nuevas vistas requieran autenticación.
3. Actualiza el `requirements.txt` si añades librerías nuevas.
