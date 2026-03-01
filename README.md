# 💼 Sistema Cartera Pro - Documentación Oficial

## 📌 Visión General
**Cartera Pro** es una plataforma integral de gestión empresarial diseñada para optimizar los procesos de cobranza, logística y ventas. El sistema combina potentes herramientas de administración financiera con un **módulo de Inteligencia Artificial (IA)** para el análisis estratégico de datos, ofreciendo una experiencia de usuario premium con una interfaz moderna y responsiva.

---

## 🏗️ Arquitectura del Sistema
El proyecto está construido sobre el robusto framework de **Django (5.2.5)**, siguiendo el patrón de diseño MVT (Modelo-Vista-Template).

### 🧱 Apps Principales
1.  **`core`**: Panel de control central (Dashboard) con métricas críticas en tiempo real.
2.  **`clientes`**: Gestión de cartera de clientes, sincronización de saldos y análisis de historial.
3.  **`productos`**: Catálogo premium con control de inventario y alta fidelidad visual.
4.  **`ventas`**: Registro de facturación, gestión de pedidos y trazabilidad.
5.  **`cartera`**: Módulo de recaudación, gestión de pagos y conciliación bancaria.
6.  **`embarques`**: Logística de envíos, gestión de costos operativos y optimización de rutas.
7.  **`modulo_ia`**: Integración con **Google Gemini 2.0 Flash** para análisis predictivo y chat interactivo con el conocimiento del negocio.

---

## 💻 Stack Tecnológico
- **Backend**: Python 3.x, Django, Django Rest Framework.
- **Base de Datos**: PostgreSQL / SQLite (Desarrollo).
- **Frontend**: Vanilla HTML5/CSS3 (Glassmorphism), JavaScript (ES6+), Bootstrap 5.3, Chart.js.
- **AI Engine**: Google Generative AI (Gemini SDK), Tenacity (Resiliencia de Red).
- **Seguridad**: `python-dotenv` para gestión de secretos, validadores de integridad a nivel de modelo.

---

## 🛠️ Características Destacadas
- **UI/UX Premium**: Diseño basado en Glassmorphism con micro-animaciones y efectos de transición suaves.
- **Integridad de Datos**: Validadores estrictos de precisión decimal (`DecimalField`) y protecciones contra valores negativos.
- **Seguridad de Acceso**: Implementación de Mixins de login y decoradores `login_required` en todas las vistas críticas.
- **Pruebas de Calidad**: Suite de más de 30 pruebas unitarias e integración que aseguran la estabilidad del código.
- **Gestión de Medios**: Optimización de carga de imágenes para productos y catálogos.

---

## 🚀 Instalación y Despliegue
1.  **Entorno Virtual**: `python -m venv venv`
2.  **Instalar Dependencias**: `pip install -r requirements.txt`
3.  **Configuración**: Crear archivo `.env` basado en el entorno de producción.
4.  **Migraciones**: `python manage.py migrate`
5.  **Servidor**: `python manage.py runserver`

---

## 🔒 Auditoría y Seguridad
El proyecto ha pasado recientemente por un ciclo de **auditoría intensiva**, reforzando la seguridad en:
- Validación de montos financieros.
- Blindaje de rutas administrativas.
- Gestión persistente de tokens de IA para optimización de costos.

---
*© 2026 CarteraPro Team - Gestión Inteligente de Cobranza.*
