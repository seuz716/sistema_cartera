# Dockerfile optimizado para producción con Python 3.12 y Gunicorn
FROM python:3.12-slim-bookworm

# 1. Configuración de variables de entorno de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 2. Instalación de dependencias del sistema requeridas para Postgres y otras herramientas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    python3-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 3. Directorio de trabajo
WORKDIR /app

# 4. Instalación de dependencias de Python
# Copiamos solo requirements primero para aprovechar la caché de capas de Docker
COPY requirements.txt /app/
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copiamos el resto del proyecto
COPY . /app/

# 6. Permisos para el script de entrada
RUN chmod +x /app/entrypoint.sh

# 7. Puerto expuesto para Gunicorn
EXPOSE 8000

# 8. Script de entrada (EntryPoint)
ENTRYPOINT ["/app/entrypoint.sh"]
